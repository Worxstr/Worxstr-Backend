import json
import datetime

from flask import jsonify, current_app, request
from flask_security import current_user, login_required, roles_required, roles_accepted

from app import db
from app.api import bp
from app.models import ScheduleShift


@bp.route('/shifts', methods=['POST'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def shifts():
	if request.method == 'POST' and request.json:
		job_id = request.args.get('job_id')
		time_begin = request.json.get('shift').get('time_begin')
		time_end = request.json.get('shift').get('time_end')
		site_location = request.json.get('shift').get('site_location')
		employee_id = request.json.get('shift').get('employee_id')
		shift = ScheduleShift(
			job_id=job_id, time_begin=time_begin, time_end=time_end, site_location=site_location, employee_id=employee_id
		)
		db.session.add(shift)
		db.session.commit()

		return jsonify({
			'success': 	True,
			'shift':	shift.to_dict()
		})

@bp.route('/shifts/<shift_id>', methods=['PUT', 'DELETE'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def shift(shift_id):
	
	if request.method == 'PUT' and request.json:
		
		shift = request.json.get('shift')

		if not shift:
			return jsonify({
				'success': False
			})

		db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).update({
			ScheduleShift.time_begin: shift.get('time_begin'),
			ScheduleShift.time_end: shift.get('time_end'),
			ScheduleShift.site_location: shift.get('site_location'),
			ScheduleShift.employee_id: shift.get('employee_id')
		})
		db.session.commit()
		shift = db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).one()

		return jsonify({
			'success': True,
			'shift': shift.to_dict()
		})
	if request.method == 'DELETE':
		db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).delete()
		db.session.commit()
		return jsonify({
			'success': True
		})


@bp.route('/shifts/next', methods=['GET'])
@login_required
@roles_accepted('employee')
def get_next_shift():
	if request.method == 'GET':
		current_time = datetime.datetime.utcnow()
		result = db.session.query(ScheduleShift).filter(ScheduleShift.employee_id == current_user.get_id(), ScheduleShift.time_end > current_time).order_by(ScheduleShift.time_end).first()
		if result == None:
			return jsonify({
				'success': True,
				'shift': None
			})
		return jsonify({
			'success': True,
			'shift': result.to_dict()
		})
	return jsonify({
		'success': False
	})
