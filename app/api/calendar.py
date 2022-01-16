from flask import request
from flask_security import current_user
from sqlalchemy.sql.elements import Null

from app import db
from app.api import bp
from app.models import ScheduleShift, TimeClock, User
from app.utils import get_request_arg


def get_events(user_id, date_begin, date_end):
    """
    Fetch all calendar shift events for a given user during a given time range.
    """
    events = []
    scheduled_shifts = (
        db.session.query(ScheduleShift)
        .filter(
            ScheduleShift.time_begin > date_begin,
            ScheduleShift.time_begin < date_end,
            ScheduleShift.contractor_id == user_id,
            ScheduleShift.active == True,
        )
        .order_by(ScheduleShift.time_begin.desc())
        .all()
    )

    for scheduled_shift in scheduled_shifts:
        shift = scheduled_shift.to_dict()

        if scheduled_shift.timecard_id != Null:
            timeclock_events = (
                db.session.query(TimeClock)
                .filter(TimeClock.timecard_id == scheduled_shift.timecard_id)
                .order_by(TimeClock.time.desc())
                .all()
            )

            shift_timeclock_events = [
                timeclock_event.to_dict() for timeclock_event in timeclock_events
            ]
            # TODO: Return a tuple of (Shift, List[TimeClock]) instead of joining
            # these types.
            shift["timeclock_events"] = shift_timeclock_events

        events.append(shift)

    return events


@bp.route("/calendar", methods=["GET"])
def get_calendar_events():
    """
    Fetch all calendar shift events for the current user or organization during
    a given time range.
    ---
    parameters:
        - name: date_begin
          in: body
          type: string
          format: date-time
          required: true
        - name: date_end
          in: body
          type: string
          format: date-time
          required: true
    responses:
        200:
            description: "A list of Shifts events. Empty, if not authenticated.
                Shifts all have the added attribute 'timeclock_events' which is
                a list of TimeClocks for a shift."
            schema:
                type: object
                properties:
                    events:
                        type: array
                        items:
                            $ref: '#/definitions/Shift'
    """
    date_begin = get_request_arg(request, "date_begin")
    date_end = get_request_arg(request, "date_end")

    events = []
    if current_user.has_role("contractor"):
        events = get_events(current_user.id, date_begin, date_end)
    elif current_user.has_role("organization_manager") or current_user.has_role(
        "contractor_manager"
    ):
        contractors = db.session.query(User).filter(User.manager_id == current_user.id)

        for contractor in [e for e in contractors if e.has_role("contractor")]:
            events.extend(get_events(contractor.id, date_begin, date_end))

    return {"events": events}
