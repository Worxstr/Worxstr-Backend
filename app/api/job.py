
from flask import jsonify, request, render_template, current_app
from flask_security import login_required, current_user
import pyqrcode
import png
from pyqrcode import QRCode

from app import db
from app.api import bp
from app.models import Job
from app.email import send_email

@bp.route('/job')
@login_required
def list_jobs():
	""" Returns list of registered jobs
	---

	responses:
		200:
			description: A list of jobs
			schema:
				$ref: '#/definitions/Job'
	"""
	result = db.session.query(Job).all()
	return jsonify(jobs=[x.to_dict() for x in result])

@bp.route('/job/add_job', methods=['POST'])
@login_required
def add_job():
	if request.method == 'POST' and request.json:
		name = request.json.get('name')
		organization_id = current_user.organization_id
		employee_manager_id = current_user.id
		organizational_manager_id = current_user.id
		address = request.json.get('address')
		city = request.json.get('city')
		state = request.json.get('state')
		zip_code = request.json.get('zip_code')
		consultant_name = request.json.get('consultant_name')
		consultant_phone = request.json.get('consultant_phone')
		consultant_email = request.json.get('consultant_email')
		consultant_code = hash(''.join([name, consultant_name, consultant_phone]))

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
                                         user=consultant_name, job=name),
               html_body=render_template('email/consultant_code.html',
                                         user=consultant_name, job=name),
				attachment='../codes/qr_code.png')

		return jsonify({
			'success': True
		})
	