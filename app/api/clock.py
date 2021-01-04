import datetime

from flask import jsonify, request
from flask_security import login_required, current_user

from app.api import bp
from app import db, security
from app.models import Job, ScheduleShift, TimeClock, TimeClockAction

@bp.route('/clock/history/<week_offset>', methods=['POST'])
@login_required
def clock_history(week_offset):
	today = datetime.datetime.combine(datetime.date.today(), datetime.datetime.max.time())
	num_weeks_begin = today - datetime.timedelta(weeks=int(week_offset))
	num_weeks_end = today - datetime.timedelta(weeks=int(week_offset)-1)
	shifts = db.session.query(TimeClock).filter(TimeClock.time > num_weeks_begin, TimeClock.time < num_weeks_end, TimeClock.employee_id == current_user.get_id()).all()

	return jsonify({
		'history': [i.to_dict() for i in shifts]
	})


@bp.route('/clock/clock_in/<shift_id>', methods=['POST'])
@login_required
def clock_in(shift_id):
	if request.method == 'POST' and request.json:
		code = str(request.json.get('code'))
		correct_code = db.session.query(Job.consultant_code).join(ScheduleShift).filter(ScheduleShift.id == shift_id).one()

		if code == correct_code[0]:
			timeclock = TimeClock(time=datetime.datetime.now(), employee_id=current_user.get_id(), action=TimeClockAction.clock_in)
			db.session.add(timeclock)
			db.session.commit()
			return jsonify({
				'success': 	True,
				'data':		timeclock.to_dict()
			})

		# TODO: Return 401 status
		return jsonify({
			'success': False
		})


@bp.route('/clock/clock_out', methods=['POST'])
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

		return jsonify({
			'success': 	True,
			'data':		timeclock.to_dict()
		})

@bp.route('/clock/start_break', methods=['POST'])
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
			'data' : timeclock.to_dict()
		})

@bp.route('/clock/end_break', methods=['POST'])
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
			'data' : timeclock.to_dict()
		})
