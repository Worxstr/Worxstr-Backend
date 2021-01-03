import json

from flask import jsonify, current_app, request
from flask_security import hash_password

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

	return jsonify(db.session.query(User.id, User.email, User.phone, User.first_name, User.last_name, User.username).all())

@bp.route('/users/register_user', methods=['POST'])
def register_user():
	if request.method == 'POST' and request.json:

		first_name = request.json.get('first_name')
		last_name = request.json.get('last_name')
		username = request.json.get('username')
		email = request.json.get('email')
		phone = request.json.get('phone')
		password = request.json.get('password')
		# TODO: Figure out how to securely store SSNs and addresses
		ssn = request.json.get('ssn')
		address = request.json.get('address')
		city = request.json.get('city')
		state = request.json.get('state')
		zip_code = request.json.get('zip_code')

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
	return jsonify(db.session.query(User.id, User.email, User.phone, User.first_name, User.last_name, User.username).filter(User.id == id).all())
