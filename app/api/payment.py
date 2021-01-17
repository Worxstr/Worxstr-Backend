from flask import jsonify, request
from flask_security import login_required, roles_accepted

from app import db
from app.api import bp
from app.models import TimeCard, User, TimeClock


@bp.route('/payments/approve', methods=['PUT'])
@bp.route('/payments/deny', methods=['PUT'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def approve_payment():
    if request.method == 'PUT' and request.json:
        ids = []
        for i in request.json.get('timecards'):
            ids.append(i['id'])
            if 'denied' in i.keys():
                db.session.query(TimeCard).filter(TimeCard.id == i['id']).update({TimeCard.denied:i['denied']}, synchronize_session = False)
            else:
                db.session.query(TimeCard).filter(TimeCard.id == i['id']).update({TimeCard.approved:i['approved'], TimeCard.paid:(not i['paypal'])}, synchronize_session = False)
        db.session.commit()
        timecards = db.session.query(TimeCard).filter(TimeCard.id.in_(ids)).all()
        result = []
        for timecard in timecards:
            temp = timecard.to_dict()
            temp["first_name"] = db.session.query(User.first_name).filter(User.id == temp["employee_id"]).one()[0]
            temp["last_name"] = db.session.query(User.last_name).filter(User.id == temp["employee_id"]).one()[0]
            temp["time_clocks"] = [ i.to_dict() for i in db.session.query(TimeClock).filter(TimeClock.timecard_id == temp["id"]).all()]
            result.append(temp)
        return jsonify({
            'success': True,
            'event': result
        })
    return jsonify({
        'success': False
    })

@bp.route('/payments/complete', methods=['PUT'])
@login_required
@roles_accepted('organization_manager', 'employee_manager')
def add_order_id():
    if request.method == 'PUT' and request.json:
        ids = []
        for i in request.json.get('timecards'):
            db.session.query(TimeCard).filter(TimeCard.id == i['id']).update({TimeCard.transaction_id:request.json.get('transaction').get("orderId")}, synchronize_session = False)
        db.session.commit()
        return jsonify({
            'success': True
        })

@bp.route('/payments/complete', methods=['PUT'])
def confirm_payment():
    return jsonify({
        'success': True
    })
