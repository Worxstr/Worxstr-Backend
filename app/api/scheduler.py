import datetime

from flask import abort, request
from flask_security import current_user, login_required,  roles_accepted

from app import db
from app.api import bp
from app.models import ScheduleShift, User


@bp.route('/shifts', methods=['POST'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def shifts():
	if not request.json:
		abort(400)

	try:
		job_id = request.args['job_id']
		time_begin = request.json['shift']['time_begin']
		time_end = request.json['shift']['time_end']
		site_location = request.json['shift']['site_location']
		employee_id = request.json['shift']['employee_id']
	except KeyError as key:
		abort(400, f"Request attribute not found: {key}")

	shift = ScheduleShift(
		job_id=job_id,
		time_begin=time_begin,
		time_end=time_end,
		site_location=site_location,
		employee_id=employee_id
	)

	db.session.add(shift)
	db.session.commit()
	result = shift.to_dict()
	result["employee"] = db.session \
		.query(User) \
		.filter(User.id == shift.employee_id) \
		.one() \
		.to_dict()
	if shift.time_begin <= datetime.datetime.utcnow() and shift.time_end >= datetime.datetime.utcnow():
		result["active"] = True

	return {'shift': result}

@bp.route('/shifts/<shift_id>', methods=['PUT', 'DELETE'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def modify_shift(shift_id):
	response = None
	if request.method == 'PUT' and request.json:
		try:
			shift = request.json['shift']
		except KeyError as key:
			abort(400, f"Request attribute not found: {key}")

		db.session \
			.query(ScheduleShift) \
			.filter(ScheduleShift.id == shift_id) \
			.update({
				ScheduleShift.time_begin: shift.get('time_begin'),
				ScheduleShift.time_end: shift.get('time_end'),
				ScheduleShift.site_location: shift.get('site_location'),
				ScheduleShift.employee_id: shift.get('employee_id')
			})

		db.session.commit()

		shift = db.session \
		.query(ScheduleShift) \
		.filter(ScheduleShift.id == shift_id) \
		.one()

		response = {'shift': shift.to_dict()}

	elif request.method == 'DELETE':
		db.session \
			.query(ScheduleShift) \
			.filter(ScheduleShift.id == shift_id) \
			.delete()
		db.session.commit()
	else:
		abort(400)

	return response


@bp.route('/shifts/next', methods=['GET'])
@login_required
@roles_accepted('employee')
def get_next_shift():
	current_time = datetime.datetime.utcnow()
	result = db.session \
		.query(ScheduleShift) \
		.filter(
			ScheduleShift.employee_id == current_user.get_id(),
			ScheduleShift.time_end > current_time
		) \
		.order_by(ScheduleShift.time_end) \
		.first()
	return {'shift': result.to_dict() if result else None}
