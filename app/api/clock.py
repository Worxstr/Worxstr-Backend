import datetime

from flask import abort, request
from flask_security import login_required, current_user, roles_accepted, roles_required

from app import db
from app.api import bp
from app.models import (
    Job,
    ScheduleShift,
    TimeClock,
    TimeClockAction,
    TimeCard,
    User,
    EmployeeInfo,
)
from app.utils import get_request_arg, get_request_json


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
        datetime.date.today(), datetime.datetime.max.time()
    )
    num_weeks_begin = today - datetime.timedelta(weeks=int(week_offset))
    num_weeks_end = today - datetime.timedelta(weeks=int(week_offset) - 1)
    shifts = (
        db.session.query(TimeClock)
        .filter(
            TimeClock.time > num_weeks_begin,
            TimeClock.time < num_weeks_end,
            TimeClock.employee_id == current_user.get_id(),
        )
        .order_by(TimeClock.time.desc())
        .all()
    )

    return {"history": [i.to_dict() for i in shifts]}


@bp.route("/clock/get-shift", methods=["GET"])
@login_required
@roles_required("employee")
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
                employee_id:
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
            ScheduleShift.employee_id == current_user.get_id(),
            ScheduleShift.time_begin > today,
        )
        .order_by(ScheduleShift.time_begin)
        .first()
    )
    return shift.to_dict()


@bp.route("/clock/clock-in", methods=["POST"])
@login_required
@roles_required("employee")
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
    shift_id = get_request_args(request, "shift_id")
    code = str(get_request_json(request, "code"))

    correct_code = (
        db.session.query(Job.consultant_code)
        .join(ScheduleShift)
        .filter(ScheduleShift.id == shift_id)
        .one()
    )

    if code != correct_code[0]:
        abort(401, "Unauthorized")

    time_in = datetime.datetime.utcnow()

    timecard = TimeCard(employee_id=current_user.get_id())
    db.session.add(timecard)
    db.session.commit()
    db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).update(
        {ScheduleShift.timecard_id: timecard.id}
    )
    timeclock = TimeClock(
        time=time_in,
        employee_id=current_user.get_id(),
        action=TimeClockAction.clock_in,
        timecard_id=timecard.id,
    )

    db.session.add(timeclock)
    db.session.commit()
    return {"event": timeclock.to_dict()}


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
    timecard_id = (
        db.session.query(TimeClock.timecard_id)
        .filter(TimeClock.employee_id == current_user.get_id())
        .order_by(TimeClock.time.desc())
        .first()
    )
    timeclock = TimeClock(
        time=time_out,
        timecard_id=timecard_id,
        employee_id=current_user.get_id(),
        action=TimeClockAction.clock_out,
    )
    db.session.add(timeclock)
    db.session.commit()
    calculate_timecard(timecard_id)
    result = timeclock.to_dict()
    result["need_info"] = (
        db.session.query(EmployeeInfo.need_info)
        .filter(EmployeeInfo.id == current_user.get_id())
        .one()[0]
    )
    return {"event": result}


@bp.route("/clock/calculate/<timecard_id>", methods=["POST"])
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
        db.session.query(EmployeeInfo.hourly_rate)
        .filter(EmployeeInfo.id == timecard.employee_id)
        .one()
    )
    wage = round(float(rate[0]) * total_time_hours, 2)
    transaction_fees = round(wage * 0.025, 2)
    total_payment = wage + transaction_fees
    # TODO: Does this need to be an iter? Can we iterate over it as a list?
    breaks = iter(
        db.session.query(TimeClock)
        .filter(
            TimeClock.employee_id == timecard.employee_id,
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
    info = (
        db.session.query(EmployeeInfo)
        .filter(EmployeeInfo.id == timecard.employee_id)
        .one()
    )
    if not info.need_info and (info.ssn is None or info.address is None):
        total_wage = 0.0
        begin_year = datetime.date(datetime.date.today().year, 1, 1)
        timecards = (
            db.session.query(TimeCard)
            .join(TimeClock)
            .filter(
                TimeCard.employee_id == timecard.employee_id,
                TimeClock.time >= begin_year,
            )
            .all()
        )
        for i in timecards:
            total_wage = total_wage + (float(i.wage_payment) - float(i.fees_payment))
        if total_wage > 400:
            db.session.query(EmployeeInfo).filter(
                EmployeeInfo.id == timecard.employee_id
            ).update({EmployeeInfo.need_info: True})
            db.session.commit()


@bp.route("/clock/timecards/<timecard_id>", methods=["PUT"])
@login_required
@roles_accepted("employee_manager")
def edit_timecard(timecard_id):
    """Edit a given timecard.
    ---
    parameters:
        - name: id
          in: body
          type: integer
          required: true
          description: TimeCard.id
        - name: changes
          in: body
          type: array
          items:
              $ref: '#/definitions/Change'
          required: true
    definitions:
        Change:
            type: object
            properties:
                id:
                    type: integer
                    description: id of the TimeClock event to be modified
                time:
                    type: string
                    format: date-time
        TimeCard:
            type: object
            properties:
                id:
                    type: integer
                time_in:
                    type: string
                    format: date-time
                time_out:
                    type: string
                    format: date-time
                time_break:
                    type: integer
                employee_id:
                    type: integer
                total_payment:
                    type: number
                approved:
                    type: boolean
                paid:
                    type: boolean
    responses:
        200:
            description: An updated TimeCard showing the new changes.
            schema:
                $ref: '#/definitions/TimeCard'
    """
    changes = get_request_json(request, "changes")

    timecard = db.session.query(TimeCard).filter(TimeCard.id == timecard_id).one()
    employee_id = timecard.employee_id

    for i in changes:
        db.session.query(TimeClock).filter(TimeClock.id == i["id"]).update(
            {TimeClock.time: i["time"]}, synchronize_session=False
        )

    db.session.commit()
    calculate_timecard(timecard.id)
    # TODO: These could likely be combined into one query
    rate = (
        db.session.query(EmployeeInfo.hourly_rate)
        .filter(EmployeeInfo.id == employee_id)
        .one()
    )
    user = (
        db.session.query(User.first_name, User.last_name)
        .filter(User.id == employee_id)
        .one()
    )
    result = (
        db.session.query(TimeCard).filter(TimeCard.id == timecard.id).one().to_dict()
    )
    result["first_name"] = user[0]
    result["last_name"] = user[1]
    result["pay_rate"] = float(rate[0])
    result["time_clocks"] = [
        timeclock.to_dict()
        for timeclock in db.session.query(TimeClock)
        .filter(TimeClock.timecard_id == timecard_id)
        .order_by(TimeClock.time)
        .all()
    ]
    return {"timecard": result}


@bp.route("/clock/timecards", methods=["GET"])
@login_required
@roles_accepted("organization_manager", "employee_manager")
def get_timecards():
    """Endpoint to get all unpaid timecards associated with the current logged in manager.
    ---
    definitions:
        TimeCard:
            type: object
            properties:
                id:
                    type: integer
                time_in:
                    type: string
                    format: date-time
                time_out:
                    type: string
                    format: date-time
                time_break:
                    type: integer
                employee_id:
                    type: integer
                total_payment:
                    type: number
                approved:
                    type: boolean
                paid:
                    type: boolean
                first_name:
                    type: string
                last_name:
                    type: string
                time_clocks:
                    type: array
                    items :
                        $ref: '#/definitions/TimeClock'
        TimeClock:
            type: object
            properties:
                id:
                    type: integer
                time:
                    type: string
                    format: date-time
                action:
                    type: string
                    enum: []
                employee_id:
                    type: integer
    responses:
        200:
            description: Returns the unapproved timecards associated with a manager
            schema:
                $ref: '#/definitions/TimeCard'
    """
    timecards = (
        db.session.query(TimeCard, User.first_name, User.last_name)
        .join(User)
        .filter(
            TimeCard.paid == False,
            TimeCard.denied == False,
            TimeCard.transaction_id == None,
            User.manager_id == current_user.get_id(),
        )
        .all()
    )

    # TODO: Implement paging here
    result = []
    print(timecards)
    for i in timecards:
        timecard = i[0].to_dict()
        print(f"Timecard: {timecard}")
        timecard["first_name"] = i[1]
        timecard["last_name"] = i[2]
        timecard["pay_rate"] = float(
            db.session.query(EmployeeInfo.hourly_rate)
            .filter(EmployeeInfo.id == timecard["employee_id"])
            .one()[0]
        )
        timecard["time_clocks"] = [
            timeclock.to_dict()
            for timeclock in db.session.query(TimeClock)
            .filter(TimeClock.timecard_id == timecard["id"])
            .order_by(TimeClock.time)
            .all()
        ]
        result.append(timecard)
    return {"timecards": result}


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
    timecard_id = (
        db.session.query(TimeClock.timecard_id)
        .filter(TimeClock.employee_id == current_user.get_id())
        .order_by(TimeClock.time.desc())
        .first()
    )
    timeclock = TimeClock(
        time=datetime.datetime.utcnow(),
        timecard_id=timecard_id,
        employee_id=current_user.get_id(),
        action=TimeClockAction.start_break,
    )
    db.session.add(timeclock)
    db.session.commit()

    return {"data": timeclock.to_dict()}


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
    timecard_id = (
        db.session.query(TimeClock.timecard_id)
        .filter(TimeClock.employee_id == current_user.get_id())
        .order_by(TimeClock.time.desc())
        .first()
    )
    timeclock = TimeClock(
        time=datetime.datetime.utcnow(),
        timecard_id=timecard_id,
        employee_id=current_user.get_id(),
        action=TimeClockAction.end_break,
    )
    db.session.add(timeclock)
    db.session.commit()

    return {"data": timeclock.to_dict()}
