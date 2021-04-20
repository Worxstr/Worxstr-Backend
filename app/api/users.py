import random
import string
import datetime

from random import randint

from flask import abort, current_app, request, render_template
from flask_security import (
	hash_password,
	current_user,
	login_required,
	roles_required,
	roles_accepted
)

from app import db, user_datastore, geolocator
from app.api import bp
from app.models import ManagerReference, User, EmployeeInfo, Organization
from app.email import send_email

@bp.route('/users', methods=['GET'])
@login_required
@roles_required('organization_manager')
def list_users():
	"""
	Returns list of registered users
	---
	responses:
		200:
			description: A list of users
			schema:
				type: array
				items:
					$ref: '#/definitions/User'
	"""
	result = db.session.query(User).all()
	return {"users": [x.to_dict() for x in result]}

@bp.route('/users/reset-password', methods=['PUT'])
@login_required
def reset_password():
	"""
	Reset the logged-in user's password
	---
	responses:
		200:
			description: Password reset successfully
	"""
	if not request.json:
		abort(400)

	try:
		new_password = request.json['password']
	except KeyError as key:
		abort(400, f"Request attribute not found: {key}")

	db.session \
		.query(User) \
		.filter(User.id == current_user.get_id()) \
		.update({User.password:hash_password(new_password)})
	db.session.commit()


@bp.route('/users/add-manager', methods=['POST'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def add_manager():
	"""
	Creates a new manager user
	---
	responses:
		200:
			description: The created manager user
			schema:
				$ref: '#/definitions/User'
	"""
	if not request.json:
		abort(400)

	try:
		first_name = request.json['first_name']
		last_name = request.json['last_name']
		username = request.json['username']
		email = request.json['email']
		phone = request.json['phone']
		roles = request.json['roles']
		manager_id = request.json['manager_id']
	except KeyError as key:
		abort(400, f"Request attribute not found: {key}")

	password = ''.join(random.choices(string.ascii_letters + string.digits, k = 10))
	confirmed_at = datetime.datetime.utcnow()
	organization_id = current_user.organization_id

	manager = user_datastore.create_user(
		first_name=first_name,
		last_name=last_name,
		username=username,
		email=email,
		phone=phone,
		roles=roles,
		manager_id=manager_id,
		organization_id=organization_id,
		confirmed_at=confirmed_at,
		password=hash_password(password)
	)
	db.session.commit()

	manager_reference = ManagerReference(
		user_id=manager.id,
		reference_number=manager_reference_generator()
	)
	db.session.add(manager_reference)
	db.session.commit()

	organization_name = db.session \
		.query(Organization.name) \
		.filter(Organization.id == organization_id) \
		.one()[0]

	send_email('[Worxstr] Welcome!',
		sender=current_app.config['ADMINS'][0],
		recipients=[email],
		text_body=render_template(
			'email/temp_password.txt',
			user=first_name,
			organization=organization_name,
			password=password
		),
		html_body=render_template(
			'email/temp_password.html',
			user=first_name,
			organization=organization_name,
			password=password
		)
	)
	return manager.to_dict()

def manager_reference_generator():
	"""
	Returns the first random number between min_ and max_ which is not already
	present in the database.
	"""
	min_ = 10000
	max_ = 1000000000
	rand = str(randint(min_, max_))

	# TODO: Generate a unique number without querying the databse in a while loop
	while db.session \
		.query(ManagerReference) \
		.filter(ManagerReference.reference_number == rand) \
		.limit(1) \
		.first() is not None:

		rand = str(randint(min_, max_))

	return rand

@bp.route('/users/add-employee', methods=['POST'])
def add_employee():
	if not request.json:
		abort(400)

	try:
		first_name = request.json['first_name']
		last_name = request.json['last_name']
		username = request.json['username']
		email = request.json['email']
		phone = request.json['phone']
		password = request.json['password']
		hourly_rate = request.json['hourly_rate']
		roles = ['employee']
		manager_id = request.json.get('manager_id', None)
	except KeyError as key:
		abort(400, f"Request attribute not found: {key}")

	organization_id = None
	confirmed_at = None

	if current_user:
		organization_id = current_user.organization_id
		organization_name = db.session \
			.query(Organization.name) \
			.filter(Organization.id == organization_id) \
			.one()[0]
		confirmed_at = datetime.datetime.utcnow()
		password = ''.join(random.choices(string.ascii_letters +  string.digits, k = 10))

	user = user_datastore.create_user(
		first_name=first_name,
		last_name=last_name,
		username=username,
		email=email,
		phone=phone,
		organization_id=organization_id,
		manager_id=manager_id,
		confirmed_at=confirmed_at,
		roles=roles,
		password=hash_password(password)
	)
	db.session.commit()

	employee_info = EmployeeInfo(id=user.id, hourly_rate=float(hourly_rate))
	db.session.add(employee_info)
	db.session.commit()

	if current_user:
		send_email('[Worxstr] Welcome!',
			sender=current_app.config['ADMINS'][0],
			recipients=[email],
			text_body=render_template(
				'email/temp_password.txt',
				user=first_name,
				organization=organization_name,
				password=password
			),
			html_body=render_template(
				'email/temp_password.html',
				user=first_name,
				organization=organization_name,
				password=password
			)
		)

	return "", 201

@bp.route('/users/check-email/<email>', methods=['GET'])
def check_email(email):
	"""
	Returns if an email does not yet exist in the database
	---
	parameters:
		- name: email
			in: path
			type: string
			required: true
	responses:
		200:
			description: True or false, if the email is unused or used, respectively
			schema:
				$ref: '#/definitions/User'
	"""
	account = db.session.query(User.id).filter(User.email == email).one_or_none()
	return {'success': account is None}, 200

@bp.route('/users/<id>', methods=['GET'])
@login_required
@roles_accepted('employee_manager', 'organization_manager')
def get_user(id):
	""" Returns a user by their ID
	---
	parameters:
		- name: id
			in: path
			type: number
			required: true
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
	result = user
	if user:
		result = user.to_dict()
		if user.has_role('employee'):
			result["employee_info"] = db.session \
				.query(EmployeeInfo) \
				.filter(EmployeeInfo.id == id) \
				.one() \
				.to_dict()
	return result, 200

@bp.route('/users/me/ssn', methods=['PUT'])
@login_required
@roles_accepted('employee')
def set_user_ssn():
	db.session \
		.query(EmployeeInfo) \
		.filter(EmployeeInfo.id == current_user.get_id()) \
		.update({
			EmployeeInfo.ssn: request.json.get("ssn")
		})
	db.session.commit()
	return "", 200

@bp.route('/users/me', methods=['GET'])
@login_required
def get_authenticated_user():
	"""
	Returns the currently authenticated user
	"""
	authenticated_user = current_user.to_dict()
	authenticated_user["roles"] = [x.to_dict() for x in current_user.roles]
	authenticated_user["organization_info"] = db.session \
		.query(Organization) \
		.filter(Organization.id == current_user.organization_id) \
		.one() \
		.to_dict()
	if current_user.has_role('employee'):
		authenticated_user["employee_info"] = db.session \
		.query(EmployeeInfo) \
		.filter(EmployeeInfo.id == current_user.get_id()) \
		.one() \
		.to_dict()
	return { "authenticated_user": authenticated_user }, 200

@bp.route('/users/edit', methods=['PUT'])
@login_required
@roles_accepted('employee')
def edit_user():
	if not request.json:
		abort(400)

	# TODO: Are all of the fields required?
	try:
		phone = request.json['phone']
		email = request.json['email']
		address = request.json['address']
		city = request.json['city']
		state = request.json['state']
		zip_code = request.json['zip_code']
	except KeyError as key:
		abort(400, f"Request attribute not found: {key}")


	db.session \
		.query(User) \
		.filter(User.id == current_user.get_id()) \
		.update({
			User.phone:phone,
			User.email:email
		})

	if current_user.has_role('employee'):
		location = geolocator.geocode(
			address + " " + city + " " + state + " " + zip_code
		)
		db.session \
			.query(EmployeeInfo) \
			.filter(EmployeeInfo.id == current_user.get_id()) \
			.update({
				EmployeeInfo.address: address,
				EmployeeInfo.city: city,
				EmployeeInfo.state: state,
				EmployeeInfo.zip_code: zip_code,
				EmployeeInfo.longitude: location.longitude,
				EmployeeInfo.latitude: location.latitude
			})

	db.session.commit()
	result = current_user.to_dict()

	if current_user.has_role('employee'):
		result["employee_info"] = db.session \
			.query(EmployeeInfo) \
			.filter(EmployeeInfo.id == current_user.get_id()) \
			.one() \
			.to_dict()

	return {"event": result}, 200

@bp.route('/users/employees', methods=['GET'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def list_employees():
	""" Returns list of employees associated with the current manager
	---

	responses:
		200:
			description: A list of users
			schema:
				$ref: '#/definitions/User'
	"""
	result = db.session \
		.query(User) \
		.filter(User.manager_id==current_user.get_id(), User.roles.any(name='employee')) \
		.all()
	return {"users": [x.to_dict() for x in result]}, 200

@bp.route('/users/employees/<id>', methods=['PUT'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def edit_employee(id):
	""" Gives manager the ability to edit an employee's pay and direct manager
	---

	responses:
		200:
	"""
	try:
		hourly_rate = request.json['hourly_rate']
	except KeyError as key:
		abort(400, f"Request attribute not found: {key}")

	db.session.query(EmployeeInfo).filter(EmployeeInfo.id == id).update({
		EmployeeInfo.hourly_rate: hourly_rate
	})
	db.session.commit()

	result = db.session.query(User).filter(User.id == id).one().to_dict()
	result["employee_info"] = db.session \
		.query(EmployeeInfo) \
		.filter(EmployeeInfo.id == id) \
		.one() \
		.to_dict()

	return {"event": result}, 200
