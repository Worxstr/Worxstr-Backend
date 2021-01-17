
from datetime import datetime
from random import randint

from flask import json, jsonify, request, render_template, current_app
from flask_security import login_required, current_user, roles_required, roles_accepted
from sqlalchemy import or_, not_
import pyqrcode
import png
from pyqrcode import QRCode

from app import db
from app.api import bp
from app.models import Job, User, ScheduleShift
from app.email import send_email

@bp.route('/jobs', methods=['GET'])
@login_required
@roles_accepted('employee_manager', 'organization_manager')
def list_jobs():
	""" Returns list of registered jobs
	---

	responses:
		200:
			description: A list of jobs
			schema:
				$ref: '#/definitions/Job'
	"""
	result = {
		"direct_jobs":[],
		"indirect_jobs":[]
	}
	direct_ids = []
	direct_jobs = db.session.query(Job).filter(or_(Job.organizational_manager_id == current_user.get_id(), Job.employee_manager_id == current_user.get_id()), Job.active == True).all()
	for direct_job in direct_jobs:
		direct_ids.append(direct_job.id)
		job = direct_job.to_dict()
		shifts = db.session.query(ScheduleShift).filter(ScheduleShift.job_id == direct_job.id, ScheduleShift.time_end > datetime.utcnow()).all()
		job["shifts"] = [shift.to_dict() for shift in shifts]
		employees = db.session.query(User).filter(User.manager_id == direct_job.employee_manager_id)
		employees_verify = []
		for i in employees:
			if i.has_role('employee'):
				employees_verify.append(i.to_dict())
		job["employees"] = employees_verify
		result["direct_jobs"].append(job)

	lower_managers = get_lower_managers(current_user.get_id())
	indirect_jobs = db.session.query(Job).filter(not_(Job.id.in_(direct_ids)), or_(Job.organizational_manager_id.in_(lower_managers), Job.employee_manager_id.in_(lower_managers)), Job.active == True).all()

	for indirect_job in indirect_jobs:
		job = indirect_job.to_dict()
		shifts = db.session.query(ScheduleShift).filter(ScheduleShift.job_id == indirect_job.id, ScheduleShift.time_end > datetime.utcnow()).all()
		job["shifts"] = [shift.to_dict() for shift in shifts]
		employees = db.session.query(User).filter(User.manager_id == indirect_job.employee_manager_id)
		employees_verify = []
		for i in employees:
			if i.has_role('employee'):
				employees_verify.append(i.to_dict())
		job["employees"] = employees_verify
		result["indirect_jobs"].append(job)

	return jsonify(result)

def get_lower_managers(manager_id):
	users = db.session.query(User).filter(User.manager_id == manager_id).all()
	lower_managers = []
	for user in users:
		if user.has_role('employee_manager') or user.has_role('organization_manager'):
			lower_managers.append(user.id)
			for i in get_lower_managers(user.id):
				lower_managers.append(i)
	return lower_managers

@bp.route('/job/add', methods=['POST'])
@login_required
@roles_required('organization_manager')
def add_job():
	if request.method == 'POST' and request.json:
		name = request.json.get('name')
		organization_id = current_user.organization_id
		employee_manager_id = request.json.get('employeeManager')
		organizational_manager_id = current_user.id
		address = request.json.get('address')
		city = request.json.get('city')
		state = request.json.get('state')
		zip_code = request.json.get('zipCode')
		consultant_name = request.json.get('consultantName')
		consultant_phone = request.json.get('consultantPhone')
		consultant_email = request.json.get('consultantEmail')
		consultant_code = str(randint(000000, 999999))

		job = Job(name=name, organization_id=organization_id, employee_manager_id=employee_manager_id, 
			organizational_manager_id=organizational_manager_id, address=address, city=city, 
			state=state, zip_code=zip_code, consultant_name=consultant_name, consultant_phone=consultant_phone, 
			consultant_email=consultant_email, consultant_code=consultant_code)
		db.session.add(job)
		db.session.commit()

		url = pyqrcode.create(consultant_code)
		url.png('codes/qr_code.png', scale = 6)

		send_email('[Worxstr] Consultant Code for ' + name,
				sender=current_app.config['ADMINS'][0],
				recipients=[consultant_email],
				text_body=render_template('email/consultant_code.txt',
										user=consultant_name, job=name, code=consultant_code),
				html_body=render_template('email/consultant_code.html',
										user=consultant_name, job=name, code=consultant_code),
				attachment='../codes/qr_code.png')

		return jsonify({
			'success': True,
			'event': job.to_dict()
		})
	return jsonify({
		'success': False
	})

@bp.route('/job/close/job_id', methods=['PUT'])
@login_required
@roles_required('organization_manager')
def close_job(job_id):
	""" Marks a given job inactive
	---
	parameters:
	- name: job_id
		in: url
		type: int
		required: true
	responses:
		200:
			description: The job that was closed
			schema:
				$ref: '#/definitions/Job'
	"""
	db.session.query(Job).filter(Job.id == job_id).update({Job.active:False})
	return jsonify({
		'success': True
	})
