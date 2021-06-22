from flask import request
from flask_security import current_user
from sqlalchemy.sql.elements import Null

from app import db
from app.api import bp
from app.models import ScheduleShift, TimeClock, User
from app.utils import get_request_arg


def get_events(user_id, date_begin, date_end):
    events = []
    scheduled_shifts = (
        db.session.query(ScheduleShift)
        .filter(
            ScheduleShift.time_begin > date_begin,
            ScheduleShift.time_begin < date_end,
            ScheduleShift.employee_id == user_id,
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
            shift["timeclock_events"] = shift_timeclock_events

        events.append(shift)

    return events


@bp.route("/calendar", methods=["GET"])
def get_calendar_events():
    date_begin = get_request_arg(request, "date_begin")
    date_end = get_request_arg(request, "date_end")

    events = []
    if current_user.has_role("employee"):
        events = get_events(current_user.get_id(), date_begin, date_end)
    elif current_user.has_role("organization_manager") or current_user.has_role(
        "employee_manager"
    ):
        employees = db.session.query(User).filter(
            User.manager_id == current_user.get_id()
        )

        for employee in [e for e in employees if e.has_role("employee")]:
            events.extend(get_events(employee.id, date_begin, date_end))

    return {"events": events}
