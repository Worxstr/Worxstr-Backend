
from flask import jsonify, request
from flask_security import current_user, login_required

from app.models import Message, User
from app.api import bp
from app import db


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = db.session.query(User).filter_by(User.id == recipient).first()
    message = Message(author=current_user, recipient=user, body=request.json.get('body'))
    db.session.add(message)
    db.session.commit()
    return jsonify({
        "success": True,
        "event": message.to_dict()
    })