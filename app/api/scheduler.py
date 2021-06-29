import datetime

from flask import abort, request
from flask_security import current_user, login_required, roles_accepted

from app import db
from app.api import bp
from app.models import ScheduleShift, User
from app.utils import get_request_arg, get_request_json, OK_RESPONSE


@bp.route("/shifts", methods=["POST"])
@login_required
@roles_accepted("organization_manager", "employee_manager")
def shifts():
    """
    Create new shifts.
    ---
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
                employee_id:
                    type: integer
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
                    shift:
                        $ref: '#/definitions/Shift'
    """
    shift = ScheduleShift.from_request(request)

    db.session.add(shift)
    db.session.commit()
    result = shift.to_dict()
    result["employee"] = (
        db.session.query(User).filter(User.id == shift.employee_id).one().to_dict()
    )
    if (
        shift.time_begin <= datetime.datetime.utcnow()
        and shift.time_end >= datetime.datetime.utcnow()
    ):
        result["active"] = True

    return {"shift": result}, 201


@bp.route("/shifts/<shift_id>", methods=["PUT"])
@login_required
@roles_accepted("organization_manager", "employee_manager")
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
            ScheduleShift.employee_id: shift.get("employee_id"),
        }
    )

    db.session.commit()

    shift = db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).one()

    return {"shift": shift.to_dict()}


@bp.route("/shifts/<shift_id>", methods=["DELETE"])
@login_required
@roles_accepted("organization_manager", "employee_manager")
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
@roles_accepted("employee")
def get_next_shift():
    """
    Get the next shift an employee is assigned to.
    ---
    responses:
        200:
            description: The next shift for the authenticated employee.
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
            ScheduleShift.employee_id == current_user.get_id(),
            ScheduleShift.time_end > current_time,
        )
        .order_by(ScheduleShift.time_end)
        .first()
    )
    return {"shift": result.to_dict() if result else None}
