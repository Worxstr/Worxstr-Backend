from flask import jsonify, request
from flask_security import login_required, roles_accepted

from app import db
from app.api import bp
from app.models import TimeCard


@bp.route('/payment/approve', methods=['POST'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def approve_payment():
    if request.method == 'POST' and request.json:
        db.session.query(TimeCard).filter(TimeCard.id == request.json.get('id')).update({TimeCard.approved:request.json.get('approved'), TimeCard.paid: (not request.json.get('paypal'))}, synchronize_session = False)
        db.session.commit()
        return jsonify({
            'success': True
        })