import datetime

from flask import jsonify, request
from flask_security import login_required, current_user

from app.api import bp
from app import db, security
from app.models import Job, ScheduleShift, TimeClock, TimeClockAction, TimeCard


@bp.route('/clock/history', methods=['GET'])
@login_required
def clock_history():

    # ? Week offset should begin at 0. There is probably a better way to write this
    week_offset = int(request.args.get('week_offset') or 0) + 1
    today = datetime.datetime.combine(
        datetime.date.today(), datetime.datetime.max.time())
    num_weeks_begin = today - datetime.timedelta(weeks=int(week_offset))
    num_weeks_end = today - datetime.timedelta(weeks=int(week_offset)-1)
    shifts = db.session.query(TimeClock).filter(TimeClock.time > num_weeks_begin,
                                                TimeClock.time < num_weeks_end, TimeClock.employee_id == current_user.get_id()).order_by(TimeClock.time.desc()).all()

    return jsonify({
        'history': [i.to_dict() for i in shifts]
    })

@bp.route('/clock/get-shift', methods=['GET'])
@login_required
def get_shift():
    today = datetime.datetime.combine(
        datetime.date.today(), datetime.datetime.min.time())
    shift = db.session.query(ScheduleShift).filter(ScheduleShift.employee_id == current_user.get_id(), ScheduleShift.time_begin > today).order_by(ScheduleShift.time_begin).first()
    return(jsonify(shift.to_dict()))

@bp.route('/clock/clock-in', methods=['POST'])
@login_required
def clock_in():
    shift_id = request.args.get('shift_id')

    if request.method == 'POST' and request.json:
        code = str(request.json.get('code'))
        correct_code = db.session.query(Job.consultant_code).join(
            ScheduleShift).filter(ScheduleShift.id == shift_id).one()

        if code == correct_code[0]:
            timeclock = TimeClock(
                time=datetime.datetime.now(), employee_id=current_user.get_id(), action=TimeClockAction.clock_in
            )
            db.session.add(timeclock)
            db.session.commit()
            return jsonify({
                'success': 	True,
                'event':		timeclock.to_dict()
            })

        # TODO: Return 401 status
        return jsonify({
            'success': False
        })


@bp.route('/clock/clock-out', methods=['POST'])
@login_required
def clock_out():
    if request.method == 'POST':
        timeclock = TimeClock(
            time=datetime.datetime.now(),
            employee_id=current_user.get_id(),
            action=TimeClockAction.clock_out
        )
        db.session.add(timeclock)
        db.session.commit()

        create_timecard(timeclock.time)

        return jsonify({
            'success': 	True,
            'event':		timeclock.to_dict()
        })

def create_timecard(time_out):
    time_in = db.session.query(TimeClock.time).filter(TimeClock.employee_id == current_user.get_id(), TimeClock.action == TimeClockAction.clock_in).order_by(TimeClock.time.desc()).first()
    breaks = iter(db.session.query(TimeClock).filter(TimeClock.employee_id == current_user.get_id(), TimeClock.time > time_in, TimeClock.time < time_out).order_by(TimeClock.time).all())
    break_time = datetime.timedelta(0)
    for x in breaks:
        y = next(breaks)
        if(x.action==TimeClockAction.start_break and y.action==TimeClockAction.end_break):
            break_time = break_time + (y.time-x.time)

    timecard = TimeCard(
        time_in=time_in,
        time_out=time_out,
        time_break=break_time,
        employee_id=current_user.get_id(),
        approved=False,
        paid=False
    )
    db.session.add(timecard)
    db.session.commit()

    return


@bp.route('/clock/start-break', methods=['POST'])
@login_required
def start_break():
    if request.method == 'POST':
        timeclock = TimeClock(
            time=datetime.datetime.now(),
            employee_id=current_user.get_id(),
            action=TimeClockAction.start_break
        )
        db.session.add(timeclock)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': timeclock.to_dict()
        })


@bp.route('/clock/end-break', methods=['POST'])
@login_required
def end_break():
    if request.method == 'POST':
        timeclock = TimeClock(
            time=datetime.datetime.now(),
            employee_id=current_user.get_id(),
            action=TimeClockAction.end_break
        )
        db.session.add(timeclock)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': timeclock.to_dict()
        })
