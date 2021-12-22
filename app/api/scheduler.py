import datetime

from flask import abort, request
from flask_security import current_user, login_required, roles_accepted
from sqlalchemy.sql.expression import desc

from app import db
from app.api import bp
from app.models import ScheduleShift, ShiftTask, User, Organization, Job
from app.scheduler import add_shift
from app.users import get_users_list
from app.utils import get_request_arg, get_request_json, get_key, OK_RESPONSE
from app.api.sockets import emit_to_users


def get_organization_user_ids(job_id):
    # Get the ids of all within the current organization from a job id
    org_id = (
        db.session.query(Organization.id).join(Job).filter(Job.id == job_id).one()[0]
    )
    return [
        r[0]
        for r in db.session.query(User.id).filter(User.organization_id == org_id).all()
    ]


@bp.route("/shifts", methods=["GET"])
@login_required
@roles_accepted("contractor")
def get_shifts():
    week_offset = int(get_request_arg(request, "week_offset") or 0) + 1
    today = datetime.datetime.combine(
        datetime.datetime.utcnow().date(), datetime.datetime.max.time()
    )
    num_weeks_begin = today - datetime.timedelta(weeks=int(week_offset))
    num_weeks_end = today - datetime.timedelta(weeks=int(week_offset) - 1)
    shifts = (
        db.session.query(ScheduleShift)
        .filter(
            ScheduleShift.time_end < num_weeks_begin,
            ScheduleShift.time_end > num_weeks_end,
            ScheduleShift.contractor_id == current_user.id,
        )
        .order_by(ScheduleShift.time_end.desc())
        .all()
    )

    return {"shifts": [i.to_dict() for i in shifts]}


@bp.route("/shifts", methods=["POST"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def shifts():
    """
    Create new shift(s).
    ---
    parameters:
        - name: job_id
          in: body
          type: integer
        - name: time_begin
          in: body
          type: string
          format: date-time
        - name: time_end
          in: body
          type: string
          format: date-time
        - name: contractor_ids
          description: Contractor IDs, in order, to be assigned to the shift.
          in: body
          type: array
          items:
              type: integer
        - name: site_locations
          description: Site locations, in order, corresponding to the respective contractor ID.
          in: body
          type: array
          items:
              type: string
    definitions:
        Shift:
            type: object
            properties:
                id:
                    type: integer
                job_id:
                    type: integer
                time_begin:
                    type: string
                    format: date-time
                time_end:
                    type: string
                    format: date-time
                contractor_id:
                    type: integer
                site_location:
                    type: string
                timecard_id:
                    type: integer
        ShiftContractorUnion:
            type: object
            description: "A Shift with the Employee added under the key 'contractor' and whether or not shift is active."
            properties:
                active:
                    type: boolean
                id:
                    type: integer
                job_id:
                    type: integer
                time_begin:
                    type: string
                    format: date-time
                time_end:
                    type: string
                    format: date-time
                contractor_id:
                    type: integer
                contractor:
                    $ref: '#/definitions/User'
                site_location:
                    type: string
                timecard_id:
                    type: integer
    responses:
        201:
            description: The newly created shift.
            schema:
                type: object
                properties:
                    shifts:
                        type: array
                        items:
                            $ref: '#/definitions/ShiftContractorUnion'
    """
    job_id = get_request_arg(request, "job_id")
    time_begin = get_request_json(request, "time_begin")
    time_end = get_request_json(request, "time_end")
    site_locations = get_request_json(request, "site_locations")
    contractor_ids = get_request_json(request, "contractor_ids")
    notes = get_request_json(request, "notes", optional=True)
    tasks = get_request_json(request, "tasks", optional=True)

    if len(site_locations) != len(contractor_ids):
        return {
            "message": "Must supply the same number of Contractor IDs and Site Locations."
        }, 400

    shifts = []
    for (e, s) in zip(contractor_ids, site_locations):
        shifts.append(
            add_shift(
                job_id,
                time_begin,
                time_end,
                site_location=s,
                contractor_id=e,
                notes=notes,
            )
        )

    contractors = get_users_list(contractor_ids)

    for s in shifts:
        for tas in tasks:
            t = ShiftTask(
                shift_id=s.id,
                description=tas["description"],
                title=tas["title"],
            )
            db.session.add(t)
    db.session.commit()

    # Add contractor objects to the results
    for s in shifts:
        setattr(
            s,
            "contractor",
            next(filter(lambda e: e.id == s.contractor_id, contractors)).to_dict(),
        )

    # Add whether or not each shift is active
    for shift in shifts:
        setattr(
            shift,
            "active",
            (
                shift.time_begin <= datetime.datetime.utcnow()
                and shift.time_end >= datetime.datetime.utcnow()
            ),
        )
    result = []
    user_ids = get_organization_user_ids(job_id)
    for s in shifts:
        shift = s.to_dict()
        next_shift = get_next_shift(s.contractor_id)["shift"]
        if next_shift != None:
            next_shift = next_shift["id"]
        result.append(shift)
        emit_to_users("ADD_SHIFT", s.to_dict(), user_ids)
        emit_to_users("ADD_EVENT", s.to_dict(), user_ids)
        emit_to_users("SET_NEXT_SHIFT", next_shift, [s.contractor_id])

    return {"shifts": result}, 201


@bp.route("/shifts/<shift_id>", methods=["PUT"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def update_shift(shift_id):
    """
    Create new shifts.
    parameters:
        - name: shift_id
          description: ID of the shift to modify.
          in: path
          type: string
          required: true
    ---
    responses:
        200:
            description: The updated shift.
            schema:
                type: object
                properties:
                    messages:
                        $ref: '#/definitions/Shift'
    """
    shift = get_request_json(request, "shift")

    db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).update(
        {
            ScheduleShift.time_begin: shift.get("time_begin"),
            ScheduleShift.time_end: shift.get("time_end"),
            ScheduleShift.site_location: shift.get("site_location"),
            ScheduleShift.contractor_id: shift.get("contractor_id"),
            ScheduleShift.notes: shift.get("notes") or ScheduleShift.notes,
        }
    )

    task_ids = (
        db.session.query(ShiftTask.id).filter(ShiftTask.shift_id == shift_id).all()
    )
    x = 0
    for i in task_ids:
        task_ids[x] = i[0]
        x += 1

    for task in shift["tasks"]:
        if "id" in task:
            task_ids.delete(task["id"])
            db.session.query(ShiftTask).filter(ShiftTask.id == task["id"]).update(
                {
                    ShiftTask.title: task["title"] or ShiftTask.title,
                    ShiftTask.description: task["description"] or ShiftTask.description,
                }
            )
        else:
            t = ShiftTask(
                shift_id=shift_id,
                description=task["description"],
                title=task["title"],
            )
            db.session.add(t)
    db.session.query(ShiftTask).filter(ShiftTask.id.in_(task_ids)).delete(
        synchronize_session="fetch"
    )
    db.session.commit()

    shift = db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).one()
    result = shift.to_dict()
    next_shift = get_next_shift(shift.contractor_id)["shift"]
    if next_shift != None:
        next_shift = next_shift["id"]
    emit_to_users("ADD_SHIFT", result, get_organization_user_ids(shift.job_id))
    emit_to_users("ADD_EVENT", result, get_organization_user_ids(shift.job_id))
    emit_to_users("SET_NEXT_SHIFT", next_shift, [shift.contractor_id])
    return {"shift": result}


@bp.route("/shifts/<shift_id>", methods=["DELETE"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def delete_shift(shift_id):
    """
    Deletes a shift.
    ---
    responses:
        200:
            description: Shift deleted.
    """
    shift = db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).one()
    job_id = shift.job_id
    contractor_id = shift.contractor_id
    db.session.query(ShiftTask).filter(ShiftTask.shift_id == shift_id).delete()
    db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).delete()
    db.session.commit()

    next_shift = get_next_shift(contractor_id)["shift"]
    if next_shift != None:
        next_shift = next_shift["id"]

    emit_to_users("REMOVE_SHIFT", int(shift_id), get_organization_user_ids(job_id))
    emit_to_users("REMOVE_EVENT", int(shift_id), get_organization_user_ids(job_id))
    emit_to_users("SET_NEXT_SHIFT", next_shift, [contractor_id])
    return OK_RESPONSE


@bp.route("/shifts/next", methods=["GET"])
@login_required
def get_next_shift(id=None):
    """
    Get the next shift an contractor is assigned to.
    ---
    responses:
        200:
            description: The next shift for the authenticated contractor.
            schema:
                type: object
                properties:
                    shift:
                        $ref: '#/definitions/Shift'
    """
    if id == None:
        id = current_user.id
    current_time = datetime.datetime.utcnow()
    result = (
        db.session.query(ScheduleShift)
        .filter(
            ScheduleShift.contractor_id == id,
            ScheduleShift.time_end > current_time,
        )
        .order_by(ScheduleShift.time_end)
        .first()
    )
    return {"shift": result.to_dict() if result else None}


@bp.route("/shifts/<shift_id>", methods=["GET"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def get_shift_id(shift_id):
    result = db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).one()
    return result.to_dict()


@bp.route("/shifts/<shift_id>/tasks", methods=["POST"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def add_shift_tasks(shift_id):
    tasks = get_request_json(request, "tasks")
    result = []
    for task in tasks:
        t = ShiftTask(
            shift_id=shift_id,
            description=task["description"],
            title=task["title"],
        )
        db.session.add(t)
        result.append(t.to_dict())
    db.session.commit()
    return result


@bp.route("/tasks/<task_id>", methods=["PUT"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def edit_shift_task(task_id):
    title = get_request_json(request, "title", optional=True)
    description = get_request_json(request, "description", optional=True)
    db.session.query(ShiftTask).filter(ShiftTask.id == task_id).update(
        {
            ShiftTask.title: title or ShiftTask.title,
            ShiftTask.description: description or ShiftTask.description,
        }
    )
    db.session.commit()
    result = db.session.query(ShiftTask).filter(ShiftTask.id == task_id).one()
    return result.to_dict()


@bp.route("/tasks/<task_id>", methods=["DELETE"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def delete_shift_task(task_id):
    db.session.query(ShiftTask).filter(ShiftTask.id == task_id).delete()
    db.session.commit()
    return OK_RESPONSE


@bp.route("/tasks/<task_id>/complete", methods=["PUT"])
@login_required
def complete_task(task_id):
    completed = get_request_json(request, "completed")
    db.session.query(ShiftTask).filter(ShiftTask.id == task_id).update(
        {
            ShiftTask.complete: completed,
            ShiftTask.last_updated: datetime.datetime.utcnow(),
        }
    )
    db.session.commit()
    result = db.session.query(ShiftTask).filter(ShiftTask.id == task_id).one()
    return result.to_dict()
