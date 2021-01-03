import datetime

from flask import jsonify, request
from flask_security import login_required, current_user

from app.api import bp
from app import db, security
from app.models import Job, ScheduleShift, TimeClock, TimeClockAction

db_test = {
	'clocked': False,
	'on_break': False,
	'users': [
		{
			'name': {
					'first': 'Alex',
					'last': 'Wohlbruck'
			}
    	},
		{
			'name': {
					'first': 'Jackson',
					'last': 'Sippe'
			}
    	}
	],
	'history': [
		{
			'id': 1,
			'time': '2021-01-02 07:36:40.034879',
			'message': 'Clocked in',
			'event_type': 'clocked_in',
			'color': 'green',
			'description': '1 min late',
		},
		{
			'id': 2,
			'time': '2021-01-02 07:36:40.034842',
			'message': 'Clocked out',
			'color': 'pink',
			'description': '5 mins left',
		},
		{
			'id': 3,
			'time': '2021-01-02 07:36:40.034724',
			'message': 'Finished break',
			'color': 'green',
			'description': '2 mins left',
		},
		{
			'id': 4,
			'time': '2021-01-02 07:36:40.034123',
			'message': 'Started break',
			'color': 'amber',
			'description': '30 mins available',
		},
		{
			'id': 5,
			'time': '2021-01-02 07:36:40.032423',
			'message': 'Clocked in',
			'color': 'green',
			'description': 'Caption',
		},
		{
			'id': 6,
			'time': '2021-01-02 07:36:40.032423',
			'message': 'Clocked in',
			'color': 'green',
			'description': 'Caption',
		}
	]
}

@bp.route('/clock', methods=['GET', 'POST'])
def clock():
	# Get clocked and break status
	if request.method == 'GET':
		return jsonify({
			'clocked': db.get('clocked'),
			'on_break': db.get('on_break')
		})

	# Update clock or break status
	#
	# Request body: {
	# 	clocked?: ['true', 'false']
	# 	on_break?: ['true', 'false']
	# }
	elif request.method == 'POST':
		if request.json:
			
			clocked = request.json.get('clocked')
			on_break = request.json.get('on_break') 

			db['clocked'] = clocked
			db['on_break'] = on_break
		
		return jsonify({
			'clocked': db['clocked'],
			'on_break': db['on_break']
		})


@bp.route('/clock/history')
def clock_history():

	# TODO: This should return the last week of timeclock history, ordered chronologically
	# TODO: Limit field will be irrelevant, each page should query 1 week of data

	limit = int(request.args.get('limit')) or 2
	offset = int(request.args.get('offset')) or 0

	return jsonify({
		'history': db_test.get('history')[(offset * limit):(limit * offset) + limit]
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
				'success': True
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
			'success': True
		})
