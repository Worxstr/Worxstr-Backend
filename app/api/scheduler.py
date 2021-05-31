import datetime

from flask import abort, request
from flask_security import current_user, login_required,  roles_accepted

from app import db
from app.api import bp
from app.models import ScheduleShift, User
from app.utils import get_request_arg, get_request_json


@bp.route('/shifts', methods=['POST'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def shifts():
	shift = ScheduleShift.from_request(request)

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
	if request.method == 'PUT':
		shift = get_request_json(request, 'shift')

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

	if request.method == 'DELETE':
		db.session \
			.query(ScheduleShift) \
			.filter(ScheduleShift.id == shift_id) \
			.delete()
		db.session.commit()

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
