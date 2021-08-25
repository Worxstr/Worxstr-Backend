import datetime

from flask import abort, request
from flask_security import current_user, login_required, roles_accepted

from app import db
from app.api import bp
from app.models import ScheduleShift, User
from app.scheduler import add_shift
from app.users import get_users_list
from app.utils import get_request_arg, get_request_json, get_key, OK_RESPONSE


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

    if len(site_locations) != len(contractor_ids):
        abort(400, "Must supply the same number of Contractor IDs and Site Locations.")

    shifts = []
    for (e, s) in zip(contractor_ids, site_locations):
        shifts.append(
            add_shift(
                job_id,
                time_begin,
                time_end,
                site_location=s,
                contractor_id=e,
            )
        )

    contractors = get_users_list(contractor_ids)

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

    return {"shifts": [s.to_dict() for s in shifts]}, 201


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
        }
    )

    db.session.commit()

    shift = db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).one()

    return {"shift": shift.to_dict()}


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
    db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).delete()
    db.session.commit()

    return OK_RESPONSE


@bp.route("/shifts/next", methods=["GET"])
@login_required
@roles_accepted("contractor")
def get_next_shift():
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
    current_time = datetime.datetime.utcnow()
    result = (
        db.session.query(ScheduleShift)
        .filter(
            ScheduleShift.contractor_id == current_user.id,
            ScheduleShift.time_end > current_time,
        )
        .order_by(ScheduleShift.time_end)
        .first()
    )
    return {"shift": result.to_dict() if result else None}
