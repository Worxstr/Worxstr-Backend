from flask import jsonify, request
from flask_security import login_required, roles_accepted

from app import db
from app.api import bp
from app.models import TimeCard


@bp.route('/payment/approve', methods=['POST'])
@bp.route('/payment/deny', methods=['POST'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def approve_payment():
    if request.method == 'POST' and request.json:
        ids = []
        for i in request.json.get('timecards'):
            ids.append(i['id'])
            db.session.query(TimeCard).filter(TimeCard.id == i['id']).update({TimeCard.approved:i['approved'], TimeCard.paid: (not i['paypal'])}, synchronize_session = False)
        db.session.commit()
        timecards = db.session.query(TimeCard).filter(TimeCard.id.in_(ids)).all()
        return jsonify({
            'success': True,
            'event': [timecard.to_dict() for timecard in timecards]
        })