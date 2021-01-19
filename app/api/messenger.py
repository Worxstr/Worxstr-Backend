from datetime import datetime

from flask import jsonify, request
from flask_socketio import emit
from flask_security import current_user, login_required

from app.models import Message, User
from app.api import bp
from app import db, socketio

@socketio.on('message')
def handle_message(data):
    print(data)


@socketio.on('connect')
def test_connect():
    print("Connected")
    emit('my response', {'data': 'Connected'})

@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = db.session.query(User).filter(User.id == recipient).first()
    message = Message(author=current_user, recipient=user, body=request.json.get('body'))
    db.session.add(message)
    db.session.commit()

    #! Socket.io
    socketio.emit('newMessage', {'message': request.json.get('body')})

    return jsonify({
        "success": True,
        "event": message.to_dict()
    })

@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).all()
    return jsonify({
        "event": [x.to_dict() for x in messages]
    })