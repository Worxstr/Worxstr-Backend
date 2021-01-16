import datetime

from flask import jsonify, request
from flask_security import login_required, current_user, roles_accepted, roles_required

from app.api import bp
from app import db, security, swagger
from app.models import Job, ScheduleShift, TimeClock, TimeClockAction, TimeCard, User, EmployeeInfo


@bp.route('/clock/history', methods=['GET'])
@login_required
def clock_history():
	"""Endpoint returning a list of TimeClock events based on the current user and week_offset.
	---
	parameters:
		- name: week_offset
			in: path
			type: int
			required: false
			default: 0
	definitions:
		TimeClock:
			type: object
			properties:
				id:
					type: int
				time:
					type: datetime
				action:
					type: enum
				employee_id:
					type: int
	responses:
		200:
			description: A list of TimeClock events. Ordered by the time of the event.
			schema:
				$ref: '#/definitions/TimeClock'
			examples:
				week_offset: 2
	"""
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
@roles_required('employee')
def get_shift():
	"""Endpoint returning the current user's next shift.
	---
	definitions:
		ScheduleShift:
			type: object
			properties:
				id:
					type: int
				job_id:
					type: int
				time_begin:
					type: datetime
				time_end:
					type: datetime
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
			datetime.date.today(), datetime.datetime.min.time())
	shift = db.session.query(ScheduleShift).filter(ScheduleShift.employee_id == current_user.get_id(), ScheduleShift.time_begin > today).order_by(ScheduleShift.time_begin).first()
	return(jsonify(shift.to_dict()))

@bp.route('/clock/clock-in', methods=['POST'])
@login_required
@roles_required('employee')
def clock_in():
	"""Endpoint to clock the current user in.
	---
	parameters:
		- name: shift_id
			in: body
			type: int
			required: true
		- name: code
			in: body
			type: int
			required: true
	definitions:
		TimeClock:
			type: object
			properties:
				id:
					type: int
				time:
					type: datetime
				action:
					type: enum
				employee_id:
					type: int
	responses:
		200:
			description: Returns the clock in TimeClock event
			schema:
				$ref: '#/definitions/TimeClock'
	"""
	shift_id = request.args.get('shift_id')

	if request.method == 'POST' and request.json:

		code = str(request.json.get('code'))
		correct_code = db.session.query(Job.consultant_code).join(
				ScheduleShift).filter(ScheduleShift.id == shift_id).one()

		if code == correct_code[0]:

			time_in = datetime.datetime.utcnow()

			timecard = TimeCard(
				employee_id=current_user.get_id()
			)
			db.session.add(timecard)
			db.session.commit()

			timeclock = TimeClock(
					time=time_in, employee_id=current_user.get_id(), 
					action=TimeClockAction.clock_in, timecard_id = timecard.id
			)
			
			db.session.add(timeclock)
			db.session.commit()
			return jsonify({
				'success': 	True,
				'event':	timeclock.to_dict()
			})

	# TODO: Return 401 status
	return jsonify({
		'success': False
	})


@bp.route('/clock/clock-out', methods=['POST'])
@login_required
def clock_out():
	"""Endpoint to clock the current user out. This method also creates a
	timecard for the shift. Clock in - Clock out.
	---
	definitions:
		TimeClock:
			type: object
			properties:
				id:
					type: int
				time:
					type: datetime
				action:
					type: enum
				employee_id:
					type: int
	responses:
		200:
			description: Returns the clock out TimeClock event
			schema:
				$ref: '#/definitions/TimeClock'
	"""
	if request.method == 'POST':
		time_out = datetime.datetime.utcnow()
		timecard_id = db.session.query(TimeClock.timecard_id).filter(TimeClock.employee_id == current_user.get_id()).order_by(TimeClock.time.desc()).first()
		timeclock = TimeClock(
			time=time_out,
			timecard_id=timecard_id,
			employee_id=current_user.get_id(),
			action=TimeClockAction.clock_out
		)
		db.session.add(timeclock)
		db.session.commit()
		calculate_timecard(timecard_id)
		return jsonify({
			'success': True,
			'event': timeclock.to_dict()
		})
	return jsonify({
		'success': False
	})

def calculate_timecard(timecard_id):
	timecard = db.session.query(TimeCard).filter(TimeCard.id == timecard_id).one()
	time_in = db.session.query(TimeClock.time).filter(TimeClock.timecard_id == timecard_id, TimeClock.action == TimeClockAction.clock_in).one()
	time_out = db.session.query(TimeClock.time).filter(TimeClock.timecard_id == timecard_id, TimeClock.action == TimeClockAction.clock_out).one()
	total_time = time_out[0] - time_in[0]
	total_time_hours = total_time.total_seconds() / 60.0 / 60.0

	rate = db.session.query(EmployeeInfo.hourly_rate).filter(EmployeeInfo.id == timecard.employee_id).one()
	wage = round(float(rate[0]) * total_time_hours, 2)

	breaks = iter(db.session.query(TimeClock).filter(
		TimeClock.employee_id == timecard.employee_id, 
		TimeClock.timecard_id == timecard.id, 
		TimeClock.action.in_((TimeClockAction.start_break, TimeClockAction.end_break))
		).order_by(TimeClock.time).all())
	break_time = datetime.timedelta(0)
	for x in breaks:
		y = next(breaks)
		if(x.action==TimeClockAction.start_break and y.action==TimeClockAction.end_break):
			break_time = break_time + (y.time-x.time)
	break_time_minutes = round(break_time.total_seconds() / 60.0, 2)
	db.session.query(TimeCard).filter(TimeCard.id == timecard_id).update({TimeCard.time_break:break_time_minutes, TimeCard.total_time:total_time_hours, TimeCard.total_payment:wage})
	db.session.commit()
	return

@bp.route('/clock/timecards/<timecard_id>', methods=['PUT'])
@login_required
@roles_accepted('employee_manager')
def edit_timecard(timecard_id):
	"""Endpoint to edit a given timecard.
	---
	parameters:
		- name: id
			in: body
			type: int
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
					type: int
					description: id of the TimeClock event to be modified
				time:
					type: datetime
		TimeCard:
			type: object
			properties:
				id:
					type: int
				time_in:
					type: datetime
				time_out:
					type: datetime
				time_break:
					type: int
				employee_id:
					type: int
				total_payment:
					type: float/numeric
				approved:
					type: bool
				paid:
					type: bool
	responses:
		200:
			description: An updated TimeCard showing the new changes.
			schema:
				$ref: '#/definitions/TimeCard'
	"""
	if request.method == 'PUT' and request.json:
		timecard = db.session.query(TimeCard).filter(TimeCard.id == timecard_id).one()
		employee_id = timecard.employee_id
		changes = request.json.get('changes')
		for i in changes:
			db.session.query(TimeClock).filter(TimeClock.id == i["id"]).update({TimeClock.time:i["time"]}, synchronize_session = False)
		calculate_timecard(timecard.id)
		rate = db.session.query(EmployeeInfo.hourly_rate).filter(EmployeeInfo.id == employee_id).one()
		user = db.session.query(User.first_name, User.last_name).filter(User.id == employee_id).one()
		result = db.session.query(TimeCard).filter(TimeCard.id == timecard.id).one().to_dict()
		result["first_name"] = user[0]
		result["last_name"] = user[1]
		result["pay_rate"] = float(rate[0])
		result["time_clocks"] = [timeclock.to_dict() for timeclock in db.session.query(TimeClock).filter(TimeClock.timecard_id == timecard_id).order_by(TimeClock.time).all()]
		return result


@bp.route('/clock/timecards', methods=['GET'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def get_timecards():
	"""Endpoint to get all unpaid timecards associated with the current logged in manager.
	---
	definitions:
		TimeCard:
			type: object
			properties:
				id:
					type: int
				time_in:
					type: datetime
				time_out:
					type: datetime
				time_break:
					type: int
				employee_id:
					type: int
				total_payment:
					type: float/numeric
				approved:
					type: bool
				paid:
					type: bool
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
					type: int
				time:
					type: datetime
				action:
					type: enum
				employee_id:
					type: int
	responses:
		200:
			description: Returns the unapproved timecards associated with a manager
			schema:
				$ref: '#/definitions/TimeCard'
	"""
	if request.method == 'GET':
		timecards = db.session.query(TimeCard, User.first_name, User.last_name).join(
			User).filter(TimeCard.paid == False, User.manager_id == current_user.get_id()).all()
		result = []
		for i in timecards:
			timecard = i[0].to_dict()
			timecard["first_name"] = i[1]
			timecard["last_name"] = i[2]
			timecard["pay_rate"] = float(db.session.query(EmployeeInfo.hourly_rate).filter(EmployeeInfo.id == timecard["employee_id"]).one()[0])
			timecard["time_clocks"] = [timeclock.to_dict() for timeclock in db.session.query(TimeClock).filter(TimeClock.timecard_id == timecard["id"]).order_by(TimeClock.time).all()]
			result.append(timecard)
		pay_rate = db.session.query(EmployeeInfo.hourly_rate).filter(EmployeeInfo.id == result[0]["employee_id"]).one()
		return jsonify({
			'success': True,
			'timecards': result
		})
	return jsonify({
		'success': False
	})

@bp.route('/clock/start-break', methods=['POST'])
@login_required
def start_break():
	"""Endpoint to start the current user's break.
	---
	definitions:
		TimeClock:
			type: object
			properties:
				id:
					type: int
				time:
					type: datetime
				action:
					type: enum
				employee_id:
					type: int
	responses:
		200:
			description: Returns the start break TimeClock event
			schema:
				$ref: '#/definitions/TimeClock'
	"""
	if request.method == 'POST':
		timecard_id = db.session.query(TimeClock.timecard_id).filter(TimeClock.employee_id == current_user.get_id()).order_by(TimeClock.time.desc()).first()
		timeclock = TimeClock(
			time=datetime.datetime.utcnow(),
			timecard_id = timecard_id,
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
	"""Endpoint to end the current user's break.
	---
	definitions:
		TimeClock:
			type: object
			properties:
				id:
					type: int
				time:
					type: datetime
				action:
					type: enum
				employee_id:
					type: int
	responses:
		200:
			description: Returns the end break TimeClock event
			schema:
				$ref: '#/definitions/TimeClock'
	"""
	if request.method == 'POST':
		timecard_id = db.session.query(TimeClock.timecard_id).filter(TimeClock.employee_id == current_user.get_id()).order_by(TimeClock.time.desc()).first()
		timeclock = TimeClock(
			time=datetime.datetime.utcnow(),
			timecard_id = timecard_id,
			employee_id=current_user.get_id(),
			action=TimeClockAction.end_break
		)
		db.session.add(timeclock)
		db.session.commit()

		return jsonify({
			'success': True,
			'data': timeclock.to_dict()
		})
