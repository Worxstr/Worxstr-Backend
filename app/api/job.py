
from datetime import datetime
from random import randint
import os

from flask import json, jsonify, request, render_template, current_app
from flask_security import login_required, current_user, roles_required, roles_accepted
from sqlalchemy import or_, not_
import pyqrcode
import png
from pyqrcode import QRCode

from app import db
from app.api import bp
from app.models import EmployeeInfo, Job, User, ScheduleShift
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
		"jobs":[],
		"managers": get_managers(current_user.manager_id or current_user.get_id())
	}

	direct_ids = []
	direct_jobs = db.session.query(Job).filter(Job.employee_manager_id == current_user.get_id(), Job.active == True).all()
	for direct_job in direct_jobs:
		job = direct_job.to_dict()
		job["direct"] = True
		result["jobs"].append(job)
		direct_ids.append(direct_job.id)

	lower_managers = get_lower_managers(current_user.get_id())
	indirect_jobs = db.session.query(Job).filter(not_(Job.id.in_(direct_ids)), or_(Job.organization_manager_id.in_(lower_managers), Job.employee_manager_id.in_(lower_managers)), Job.active == True).all()

	for indirect_job in indirect_jobs:
		job = indirect_job.to_dict()
		job["direct"] = False
		result["jobs"].append(job)

	return jsonify(result)

	
@bp.route('/jobs', methods=['POST'])
@login_required
@roles_required('organization_manager')
def add_job():
	if request.method == 'POST' and request.json:
		name = request.json.get('name')
		organization_id = current_user.organization_id
		employee_manager_id = request.json.get('employee_manager')
		organization_manager_id = current_user.id
		address = request.json.get('address')
		city = request.json.get('city')
		state = request.json.get('state')
		country = request.json.get('country')
		zip_code = request.json.get('zip_code')
		longitude = request.json.get('longitude')
		latitude = request.json.get('latitude')
		consultant_name = request.json.get('consultant_name')
		consultant_phone = request.json.get('consultant_phone')
		consultant_email = request.json.get('consultant_email')
		consultant_code = str(randint(000000, 999999))

		job = Job(name=name, organization_id=organization_id, employee_manager_id=employee_manager_id, 
			organization_manager_id=organization_manager_id, address=address, city=city, 
			state=state, zip_code=zip_code, country=country, consultant_name=consultant_name, consultant_phone=consultant_phone, 
			consultant_email=consultant_email, consultant_code=consultant_code,
			longitude=longitude, latitude=latitude)
		db.session.add(job)
		db.session.commit()

		send_consultant_code(job.id)

		return jsonify({
			'success': True,
			'job': job.to_dict()
		})
	return jsonify({
		'success': False
	})

@bp.route('/jobs/<job_id>', methods=['GET'])
@login_required
@roles_accepted('employee_manager', 'organization_manager')
def job_detail(job_id):
	job = db.session.query(Job).filter(Job.id == job_id).one().to_dict()
	scheduled_shifts = db.session.query(ScheduleShift).filter(ScheduleShift.job_id == job['id'], ScheduleShift.time_begin > datetime.utcnow()).all()
	active_shifts = db.session.query(ScheduleShift).filter(
		ScheduleShift.job_id == job['id'],
		ScheduleShift.time_begin <= datetime.utcnow(),
		ScheduleShift.time_end >= datetime.utcnow()
	).all()
	shifts = []

	for i in scheduled_shifts:
		shifts.append(i.to_dict())
	for i in active_shifts:
		shift = i.to_dict()
		shift["active"] = True
		shifts.append(shift)

	job["shifts"] = shifts
	job["managers"] = get_managers(current_user.manager_id or current_user.get_id())
	job["employees"] = []
	employees = db.session.query(User).filter(User.manager_id == job['employee_manager_id'])
	for i in employees:
		if i.has_role('employee'):
			employee = i.to_dict()
			employee_info = db.session.query(EmployeeInfo).filter(EmployeeInfo.id == i.id).one().to_dict()
			employee["employee_info"] = employee_info
			job["employees"].append(employee)
	return jsonify(job = job)

@login_required
@roles_accepted('employee_manager', 'organization_manager')
@bp.route('/jobs/managers/<manager_id>', methods=['GET'])
def get_managers(manager_id):
	managers = get_lower_managers(manager_id)
	result = {'organization_managers':[],'employee_managers':[]}
	for i in managers:
		user = db.session.query(User).filter(User.id == i).one()
		if user.has_role('organization_manager'):
			result['organization_managers'].append(user.to_dict())
		if user.has_role('employee_manager'):
			result['employee_managers'].append(user.to_dict())
	if current_user.has_role('organization_manager'):
		result['organization_managers'].append(current_user.to_dict())
	if current_user.has_role('employee_manager'):
		result['employee_managers'].append(current_user.to_dict())
	return result

def get_lower_managers(manager_id):
	users = db.session.query(User).filter(User.manager_id == manager_id, User.organization_id == current_user.organization_id).all()
	lower_managers = []
	for user in users:
		if user.has_role('employee_manager') or user.has_role('organization_manager'):
			lower_managers.append(user.id)
			for i in get_lower_managers(user.id):
				lower_managers.append(i)
	return lower_managers

@bp.route('/jobs/<job_id>', methods=['PUT'])
@login_required
@roles_required('organization_manager')
def edit_job(job_id):
	if request.method == 'PUT' and request.json:
		job = db.session.query(Job).filter(Job.id == job_id).one()
		original_email = job.consultant_email
		original_code = job.consultant_code
		db.session.query(Job).filter(Job.id == job_id).update({
			Job.name: request.json.get('name'),
			Job.employee_manager_id: request.json.get('employee_manager_id'),
			Job.organization_manager_id: request.json.get('organization_manager_id'),
			Job.address: request.json.get('address'),
			Job.city: request.json.get('city'),
			Job.state: request.json.get('state'),
			Job.zip_code: request.json.get('zip_code'),
			Job.longitude: request.json.get('longitude'),
			Job.latitude: request.json.get('latitude'),
			Job.consultant_name: request.json.get('consultant_name'),
			Job.consultant_phone: request.json.get('consultant_phone'),
			Job.consultant_email: request.json.get('consultant_email')
		})
		if request.json.get('generateNewCode'):
			db.session.query(Job).filter(Job.id == job_id).update({
				Job.consultant_code: str(randint(000000, 999999))
			})
		db.session.commit()

		if job.consultant_email != original_email or job.consultant_code != original_code:
			send_consultant_code(job.id)
		return jsonify({
			'success': True,
			'job': job.to_dict()
		})
	return jsonify({
		'success': False
	})

def send_consultant_code(job_id):
	job = db.session.query(Job).filter(Job.id == job_id).one()
	url = pyqrcode.create(job.consultant_code)
	if not os.path.exists('codes'):
		os.makedirs('codes')
	url.png('codes/qr_code.png', scale = 6)

	send_email('[Worxstr] Consultant Code for ' + job.name,
			sender=current_app.config['ADMINS'][0],
			recipients=[job.consultant_email],
			text_body=render_template('email/consultant_code.txt',
									user=job.consultant_name, job=job.name, code=job.consultant_code),
			html_body=render_template('email/consultant_code.html',
									user=job.consultant_name, job=job.name, code=job.consultant_code),
			attachment='../codes/qr_code.png')

@bp.route('/jobs/<job_id>/close', methods=['PUT'])
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
	db.session.commit()
	return jsonify({
		'success': True
	})