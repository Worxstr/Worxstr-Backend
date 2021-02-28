from datetime import datetime
from random import randint

from flask import jsonify, request
from flask_socketio import emit
from flask_security import current_user, login_required

from app.models import Message, User, Conversation
from app.api import bp
from app import db, socketio

@socketio.on('connect')
def on_connect():
    # TODO: Attach the client session id to the user data in DB
    print("Client connected")

'''
TODO:
I have implemented some basic messaging so far. You can send messages from different user accounts,
and the messages that other users have send appear on the left, and your messages on the right.

I mapped employeeone@worxstr.com to name Jackson Sippe and managerone@worxstr.com to Alex Wohlbruck,
so when logged in to those accounts, the names appear next to the message.

Right now the new messages are broadcasted to all clients. We need to attach the socket.io session ids
to each user account so that we can filter the broadcasts to certain clients.
'''

@bp.route('/conversations', methods=['GET', 'POST'])
@login_required
def conversations():
    # List conversations
    if request.method == 'GET':
        conversations = db.session.query(Conversation).all()
        return jsonify({
            'conversations': [conversation.to_dict() for conversation in conversations]
        })
    if request.method == 'POST':
        participants = [current_user]
        for i in request.json.get('users'):
            participants.append(db.session.query(User).filter(User.id==i).one())
        conversation = Conversation(participants=participants)
        db.session.add(conversation)
        db.session.commit()
        return jsonify({
            "conversation": conversation.to_dict()
        })

@bp.route('/conversations/contacts', methods=['GET'])
@login_required
def contacts():
    if request.method == 'GET':
        contacts = db.session.query(User).filter(User.organization_id==current_user.organization_id).all()
        return jsonify({
            'contacts': [contact.to_dict() for contact in contacts]
        })

@bp.route('/conversations/<conversation_id>', methods=['GET'])
@login_required
def conversation(conversation_id):
    # Get conversation data along with messages
    if request.method == 'GET':

        conversation = db.session.query(Conversation).filter(Conversation.id == conversation_id).one()
        return jsonify({
            'conversation': conversation.to_dict()
        })

@bp.route('/conversations/<conversation_id>/messages', methods=['GET', 'POST'])
@login_required
def messages(conversation_id):

    # List messages in a conversation
    if request.method == 'GET':
        # The last message id that was recieved by the client.
        # Return the most recent if not set
        last_id = request.args.get('last_id')

        # The amount of messages to return
        limit = request.args.get('limit')

        # TODO: Query the messages for a given last_id and limit
        messages = db.session.query(Message).filter(Message.conversation_id == conversation_id).all()

        return jsonify({
            'messages': [message.to_dict() for message in messages]
        }) 

    # Send a message
    if request.method == 'POST':
        return jsonify({
            'message': send_message(conversation_id, current_user.get_id(), {
                'body': request.json.get('body')
            })
        })

def send_message(conversation_id, user_id, message):
    # TODO: Get user ID from database by querying for socket session id

    db_message = Message (
        sender_id=user_id,
        body=message.get('body'),
        conversation_id=conversation_id
    )
    db.session.add(db_message)
    db.session.commit()

    socket_message = {
        'id': db_message.id,
        'conversation_id': conversation_id,
        'sender_id': user_id,
        'body': message.get('body')
    }

    socketio.emit('message:create', {
        'message': socket_message,
        'conversation_id': conversation_id
    })

    return socket_message