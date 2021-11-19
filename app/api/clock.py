import datetime

from flask import abort, request
from flask_security import login_required, current_user, roles_accepted, roles_required

from app import db
from app.api import bp
from app.api.sockets import emit_to_users
from app.models import (
    Job,
    ScheduleShift,
    TimeClock,
    TimeClockAction,
    TimeCard,
    User,
    ContractorInfo,
    Role,
)
from app.utils import get_request_arg, get_request_json


def get_manager_user_ids(organization_id):
    # Get the ids of managers within the current organization
    return [
        r[0]
        for r in db.session.query(User.id)
        .filter(
            User.organization_id == organization_id,
            User.roles.any(
                Role.name.in_(["contractor_manager", "organization_manager"])
            ),
        )
        .all()
    ]


@bp.route("/clock/history", methods=["GET"])
@login_required
def clock_history():
    """
    Endpoint returning a list of TimeClock events based on the current user and week_offset.
    ---
    parameters:
        - name: week_offset
          in: path
          type: integer
          required: false
          default: 0
    responses:
        200:
            description: A list of TimeClock events. Ordered by the time of the event.
            schema:
                $ref: '#/definitions/TimeClock'
            examples:
                week_offset: 2
    """
    # ? Week offset should begin at 0. There is probably a better way to write this
    week_offset = int(get_request_arg(request, "week_offset") or 0) + 1
    today = datetime.datetime.combine(
        datetime.datetime.utcnow().date(), datetime.datetime.max.time()
    )
    num_weeks_begin = today - datetime.timedelta(weeks=int(week_offset))
    num_weeks_end = today - datetime.timedelta(weeks=int(week_offset) - 1)
    shifts = (
        db.session.query(TimeClock)
        .filter(
            TimeClock.time > num_weeks_begin,
            TimeClock.time < num_weeks_end,
            TimeClock.contractor_id == current_user.id,
        )
        .order_by(TimeClock.time.desc())
        .all()
    )

    return {"history": [i.to_dict() for i in shifts]}


@bp.route("/clock/get-shift", methods=["GET"])
@login_required
@roles_required("contractor")
def get_shift():
    """Endpoint returning the current user's next shift.
    ---
    definitions:
        ScheduleShift:
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
                    type: int
                site_location:
                    type: string
    responses:
        200:
            description: A single ScheduleShift object. This is the current users next shift.
            schema:
                $ref: '#/definitions/ScheduleShift'
    """
    today = datetime.datetime.combine(
        datetime.date.today(), datetime.datetime.min.time()
    )
    shift = (
        db.session.query(ScheduleShift)
        .filter(
            ScheduleShift.contractor_id == current_user.id,
            ScheduleShift.time_begin > today,
        )
        .order_by(ScheduleShift.time_begin)
        .first()
    )
    return shift.to_dict()


@bp.route("/clock/clock-in", methods=["POST"])
@login_required
@roles_required("contractor")
def clock_in():
    """
    Clock the current user in.
    ---
    parameters:
        - name: shift_id
          in: body
          type: integer
          required: true
        - name: code
          in: body
          type: integer
          required: true
    responses:
        200:
            description: Returns the clock in TimeClock event
            schema:
                $ref: '#/definitions/TimeClock'
    """
    shift_id = get_request_arg(request, "shift_id")
    code = str(get_request_json(request, "code"))
    job = (
        db.session.query(Job)
        .join(ScheduleShift)
        .filter(ScheduleShift.id == shift_id)
        .one()
    )
    correct_code = job.consultant_code

    if code != correct_code:
        return {"message": "Invalid clock-in code."}, 401

    timeclock_state = (
        db.session.query(TimeClock.action)
        .filter(TimeClock.contractor_id == current_user.id)
        .order_by(TimeClock.time.desc())
        .first()
    )
    if timeclock_state != None:
        if (
            timeclock_state[0] == TimeClockAction.clock_in
            or timeclock_state[0] == TimeClockAction.start_break
            or timeclock_state[0] == TimeClockAction.end_break
        ):
            return {"message": "User is currently clocked in"}, 409

    time_in = datetime.datetime.utcnow()

    timecard = TimeCard(contractor_id=current_user.id)
    db.session.add(timecard)
    db.session.commit()
    db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).update(
        {ScheduleShift.timecard_id: timecard.id}
    )
    timeclock = TimeClock(
        time=time_in,
        contractor_id=current_user.id,
        action=TimeClockAction.clock_in,
        timecard_id=timecard.id,
        shift_id=shift_id,
        job_id=job.id,
    )

    db.session.add(timeclock)
    db.session.commit()

    payload = timeclock.to_dict()
    user_ids = get_manager_user_ids(current_user.organization_id)
    user_ids.append(current_user.id)
    emit_to_users("ADD_CLOCK_EVENT", payload, user_ids)
    return payload


@bp.route("/clock/clock-out", methods=["POST"])
@login_required
def clock_out():
    """
    Clock the current user out, creating a timecard for the shift:
    Clock in -> Clock out.
    ---
    responses:
        200:
            description: Returns the clock out TimeClock event
            schema:
                $ref: '#/definitions/TimeClock'
    """
    time_out = datetime.datetime.utcnow()
    timecard_info = (
        db.session.query(TimeClock)
        .filter(TimeClock.contractor_id == current_user.id)
        .order_by(TimeClock.time.desc())
        .first()
    )

    if timecard_info.action == TimeClockAction.clock_out:
        return {"message": "Already clocked out"}, 409

    timeclock = TimeClock(
        time=time_out,
        timecard_id=timecard_info.timecard_id,
        contractor_id=current_user.id,
        action=TimeClockAction.clock_out,
        shift_id=timecard_info.shift_id,
        job_id=timecard_info.job_id,
    )
    db.session.add(timeclock)
    db.session.commit()
    calculate_timecard(timecard_info.timecard_id)

    payload = timeclock.to_dict()
    timecard = (
        db.session.query(TimeCard)
        .filter(TimeCard.id == timecard_info.timecard_id)
        .one()
        .to_dict()
    )
    timecard["time_clocks"] = []
    time_clocks = (
        db.session.query(TimeClock)
        .filter(TimeClock.timecard_id == timecard_info.timecard_id)
        .all()
    )
    for time_clock in time_clocks:
        timecard["time_clocks"].append(time_clock.to_dict())
    user_ids = get_manager_user_ids(current_user.organization_id)
    emit_to_users("ADD_TIMECARD", timecard, user_ids)
    user_ids.append(current_user.id)
    emit_to_users("ADD_CLOCK_EVENT", payload, user_ids)
    return payload


@bp.route("/clock/start-break", methods=["POST"])
@login_required
def start_break():
    """Endpoint to start the current user's break.
    ---
    responses:
        200:
            description: Returns the start break TimeClock event
            schema:
                $ref: '#/definitions/TimeClock'
    """
    timecard_info = (
        db.session.query(TimeClock)
        .filter(TimeClock.contractor_id == current_user.id)
        .order_by(TimeClock.time.desc())
        .first()
    )

    if timecard_info.action == TimeClockAction.start_break:
        return {"message": "Already on break"}, 409
    if timecard_info.action == TimeClockAction.clock_out:
        return {"message": "Not currently clocked in"}, 409

    timeclock = TimeClock(
        time=datetime.datetime.utcnow(),
        timecard_id=timecard_info.timecard_id,
        contractor_id=current_user.id,
        action=TimeClockAction.start_break,
        shift_id=timecard_info.shift_id,
        job_id=timecard_info.job_id,
    )
    db.session.add(timeclock)
    db.session.commit()

    payload = timeclock.to_dict()
    user_ids = get_manager_user_ids(current_user.organization_id)
    user_ids.append(current_user.id)
    emit_to_users("ADD_CLOCK_EVENT", payload, user_ids)
    return payload


@bp.route("/clock/end-break", methods=["POST"])
@login_required
def end_break():
    """Endpoint to end the current user's break.
    ---
    responses:
        200:
            description: Returns the end break TimeClock event
            schema:
                $ref: '#/definitions/TimeClock'
    """
    timecard_info = (
        db.session.query(TimeClock)
        .filter(TimeClock.contractor_id == current_user.id)
        .order_by(TimeClock.time.desc())
        .first()
    )

    if timecard_info.action == TimeClockAction.end_break:
        return {"message": "Not currently on break"}, 409
    if timecard_info.action == TimeClockAction.clock_out:
        return {"message": "Not currently clocked in"}, 409

    timeclock = TimeClock(
        time=datetime.datetime.utcnow(),
        timecard_id=timecard_info.timecard_id,
        contractor_id=current_user.id,
        action=TimeClockAction.end_break,
        shift_id=timecard_info.shift_id,
        job_id=timecard_info.job_id,
    )
    db.session.add(timeclock)
    db.session.commit()

    payload = timeclock.to_dict()
    user_ids = get_manager_user_ids(current_user.organization_id)
    user_ids.append(current_user.id)
    emit_to_users("ADD_CLOCK_EVENT", payload, user_ids)
    return payload


def calculate_timecard(timecard_id):
    """
    Calculate pay for a given timecard and update the timecard in place.
    ---
    parameters:
        - name: timecard_id
          in: path
          type: integer
          required: true
    """
    timecard = db.session.query(TimeCard).filter(TimeCard.id == timecard_id).one()
    time_in = (
        db.session.query(TimeClock.time)
        .filter(
            TimeClock.timecard_id == timecard_id,
            TimeClock.action == TimeClockAction.clock_in,
        )
        .one()
    )
    time_out = (
        db.session.query(TimeClock.time)
        .filter(
            TimeClock.timecard_id == timecard_id,
            TimeClock.action == TimeClockAction.clock_out,
        )
        .one()
    )
    total_time = time_out[0] - time_in[0]
    total_time_hours = total_time.total_seconds() / 60.0 / 60.0

    rate = (
        db.session.query(ContractorInfo.hourly_rate)
        .filter(ContractorInfo.id == timecard.contractor_id)
        .one()
    )
    wage = round(float(rate[0]) * total_time_hours, 2)
    transaction_fees = round(wage * 0.02, 2)
    total_payment = wage + transaction_fees
    # TODO: Does this need to be an iter? Can we iterate over it as a list?
    breaks = iter(
        db.session.query(TimeClock)
        .filter(
            TimeClock.contractor_id == timecard.contractor_id,
            TimeClock.timecard_id == timecard.id,
            TimeClock.action.in_(
                (TimeClockAction.start_break, TimeClockAction.end_break)
            ),
        )
        .order_by(TimeClock.time)
        .all()
    )
    break_time = datetime.timedelta(0)
    # TODO: Make these variables more intuitive
    for x in breaks:
        y = next(breaks)
        if (
            x.action == TimeClockAction.start_break
            and y.action == TimeClockAction.end_break
        ):
            break_time = break_time + (y.time - x.time)
    break_time_minutes = round(break_time.total_seconds() / 60.0, 2)
    db.session.query(TimeCard).filter(TimeCard.id == timecard_id).update(
        {
            TimeCard.time_break: break_time_minutes,
            TimeCard.total_time: total_time_hours,
            TimeCard.total_payment: total_payment,
            TimeCard.wage_payment: wage,
            TimeCard.fees_payment: transaction_fees,
        }
    )
    db.session.commit()
