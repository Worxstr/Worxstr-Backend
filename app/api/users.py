import json

from flask import jsonify, current_app, request
from flask_security import hash_password, current_user, login_required

from app import db, user_datastore
from app.api import bp
from app.models import User, EmployeeInfo

@bp.route('/users')
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

@bp.route('/users/add_employee', methods=['POST'])
def add_employee():
	if request.method == 'POST' and request.json:

		first_name = request.json.get('firstName')
		last_name = request.json.get('lastName')
		username = request.json.get('username')
		email = request.json.get('email')
		phone = request.json.get('phone')
		password = request.json.get('password')
		# TODO: Figure out how to securely store SSNs and addresses
		ssn = request.json.get('ssn')
		address = request.json.get('address')
		city = request.json.get('city')
		state = request.json.get('state')
		zip_code = request.json.get('zipCode')

		user = user_datastore.create_user(first_name=first_name, last_name=last_name, username=username, email=email, phone=phone, password=hash_password(password))
		db.session.commit()

		employee_info = EmployeeInfo(id=user.id, ssn=ssn, address=address, city=city, state=state, zip_code=zip_code)
		db.session.add(employee_info)
		db.session.commit()

		return jsonify({
			'success': True
		})

@bp.route('/users/check_email/<email>')
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
	result = db.session.query(User).filter(User.id == id).one_or_none()
	return jsonify(result.to_dict())

@bp.route('/users/me')
@login_required
def get_authenticated_user():
	""" Returns the currently authenticated user
	"""
	return jsonify(authenticated_user=current_user.to_dict())
