import json
from random import randint

from flask import jsonify, current_app, request
from flask_security import hash_password, current_user, login_required, roles_required, roles_accepted

from app import db, user_datastore, geolocator
from app.api import bp
from app.models import ManagerReference, User, EmployeeInfo, Organization

@bp.route('/users')
@login_required
@roles_required('organization_manager')
def list_users():
	""" Returns list of registered users
	---
	
	responses:
		200:
			description: A list of users
			schema:
				$ref: '#/definitions/User'
	"""
	result = db.session.query(User).all()
	return jsonify(users=[x.to_dict() for x in result])

@bp.route('/users/add-manager', methods=['POST'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def add_manager():
	if request.method == 'POST' and request.json:
		first_name = request.json.get('firstName')
		last_name = request.json.get('lastName')
		username = request.json.get('username')
		email = request.json.get('email')
		phone = request.json.get('phone')
		password = request.json.get('password')
		roles = request.json.get('roles')
		manager_id = request.json.get('managerId')
		manager = user_datastore.create_user(first_name=first_name, last_name=last_name, username=username, email=email, phone=phone, roles=roles, manager_id=manager_id, password=hash_password(password))
		db.session.commit()
		manager_reference = ManagerReference(user_id=manager.id, reference_number=manager_reference_generator())
		db.session.add(manager_reference)
		db.session.commit()
		return jsonify({
			'event': manager.to_dict(),
			'success': True
		})
	return jsonify({
		'success': False
	})

def manager_reference_generator():
	min_ = 10000
	max_ = 1000000000
	rand = str(randint(min_, max_))

	while db.session.query(ManagerReference).filter(ManagerReference.reference_number == rand).limit(1).first() is not None:
		rand = str(randint(min_, max_))
	return rand

@bp.route('/users/add-employee', methods=['POST'])
def add_employee():
	if request.method == 'POST' and request.json:

		first_name = request.json.get('firstName')
		last_name = request.json.get('lastName')
		username = request.json.get('username')
		email = request.json.get('email')
		phone = request.json.get('phone')
		password = request.json.get('password')
		roles = ['employee']

		user = user_datastore.create_user(first_name=first_name, last_name=last_name, username=username, email=email, phone=phone, roles=roles, password=hash_password(password))
		db.session.commit()
		employee_info = EmployeeInfo(id=user.id)
		db.session.add(employee_info)
		db.session.commit()

		return jsonify({
			'success': True
		})
	return jsonify({
		'success': False
	})

@bp.route('/users/check-email/<email>')
def check_email(email):
	account = db.session.query(User.id).filter(User.email == email).one_or_none()
	if account == None:
		return jsonify({
			'success': True
		})
	return jsonify({
		'success': False
	})

@bp.route('/users/<id>')
@login_required
@roles_accepted('employee_manager', 'organization_manager')
def get_user(id):
	""" Returns a user by their ID
	---
	# parameters:
	# 	- name: id
	# 		in: path
	# 		type: number
	# 		required: true
	definitions:
		User:
			type: object
			properties:
				first:
					type: string
					example: Jackson
				last:
					type: string
					example: Sippe
	responses:
		200:
			description: The specified user
			schema:
				$ref: '#/definitions/User'
	"""
	user = db.session.query(User).filter(User.id == id).one_or_none()
	return jsonify(user.to_dict())

@bp.route('/users/me', methods=['GET'])
@login_required
def get_authenticated_user():
	""" Returns the currently authenticated user
	"""
	authenticated_user = current_user.to_dict()
	authenticated_user["roles"] = [x.to_dict() for x in current_user.roles]
	authenticated_user["organization_info"] = db.session.query(Organization).filter(Organization.id == current_user.organization_id).one().to_dict()
	if current_user.has_role('employee'):
		authenticated_user["employee_info"] = db.session.query(EmployeeInfo).filter(EmployeeInfo.id == current_user.get_id()).one().to_dict()
	return jsonify(authenticated_user=authenticated_user)

@bp.route('/users/edit', methods=['PUT'])
@login_required
def edit_user():
	if request.method == 'PUT' and request.json:
		db.session.query(User).filter(User.id == current_user.get_id()).update({User.phone:request.json.get('phone'), User.email:request.json.get('email')})
		if current_user.has_role('employee'):
			location = geolocator.geocode(
				request.json.get('address') + " " + request.json.get('city') + " " + request.json.get('state') + " " + request.json.get('zipCode')
			)
			db.session.query(EmployeeInfo).filter(EmployeeInfo.id == current_user.get_id()).update({
				EmployeeInfo.address: request.json.get('address'),
				EmployeeInfo.city: request.json.get('city'),
				EmployeeInfo.state: request.json.get('state'),
				EmployeeInfo.zip_code: request.json.get('zipCode'),
				EmployeeInfo.longitude: location.longitude,
				EmployeeInfo.latitude: location.latitude
			})
		db.session.commit()
		result = current_user.to_dict()
		if current_user.has_role('employee'):
			result["employee_info"] = db.session.query(EmployeeInfo).filter(EmployeeInfo.id == current_user.get_id()).one().to_dict()
		return jsonify({
			"success": True,
			"event": result
		})
	return jsonify({
		"success": False
	})
