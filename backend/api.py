from flask import Blueprint, jsonify

api = Blueprint('api', __name__, url_prefix='/api')

db = {
	'users': [
		{
			'name': {
					'first': 'Alex',
					'last': 'Wohlbruck'
			}
    },
		{
			'name': {
					'first': 'Jackson',
					'last': 'Sippe'
			}
    	}
	]
}
    
@api.route('/users')
def list_users():
	""" Returns list of registered users
	---
	
	responses:
		200:
			description: A list of users
			schema:
				$ref: '#/definitions/User'
	"""
	return jsonify(db.get('users'))

@api.route('/users/<id>')
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

	return jsonify(db.get('users')[int(id)])
