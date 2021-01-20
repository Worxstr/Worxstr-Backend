import json
import datetime

from flask import jsonify, current_app, request
from flask_security import current_user, login_required, roles_required, roles_accepted

from app import db
from app.api import bp
from app.models import ScheduleShift


@bp.route('/shifts/<shift_id>', methods=['GET', 'POST', 'PUT'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def shifts(shift_id):
	if request.method == 'POST' and request.json:
		time_begin = request.json.get('timeBegin')
		time_end = request.json.get('timeEnd')
		site_location = request.json.get('siteLocation')

		shift = ScheduleShift(
			job_id=job_id, time_begin=time_begin, time_end=time_end, site_location=site_location
		)
		db.session.add(shift)
		db.session.commit()

		return jsonify({
			'success': 	True,
			'event':	shift.to_dict()
		})

	if request.method == 'PUT' and request.json:
        db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).update({
            ScheduleShift.time_begin: request.json.get('timeBegin'),
            ScheduleShift.time_end: request.json.get('timeEnd'),
            ScheduleShift.site_location: request.json.get('siteLocation'),
            ScheduleShift.employee_id: request.json.get('employeeId')
        })
        db.session.commit()
        shift = db.session.query(ScheduleShift).filter(ScheduleShift.id == shift_id).one()

        return jsonify({
            'success': True,
            'event': shift.to_dict()
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
				'event': None
			})
		return jsonify({
			'success': True,
			'event': result.to_dict()
		})
	return jsonify({
		'success': False
	})
