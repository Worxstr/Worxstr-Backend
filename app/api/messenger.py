from datetime import datetime
from random import randint

from flask import jsonify, request
from flask_socketio import emit
from flask_security import current_user, login_required

from app.models import Message, User, Conversation
from app.api import bp
from app import db, socketio


@socketio.on('connect')
def test_connect():
    # TODO: Attach the client session id to the user data in DB
    print("Client connected")


###################
###################
# Temporary code #

'''
TODO:
I have implemented some basic messaging so far. You can send messages from different user accounts,
and the messages that other users have send appear on the left, and your messages on the right.

I mapped employeeone@worxstr.com to name Jackson Sippe and managerone@worxstr.com to Alex Wohlbruck,
so when logged in to those accounts, the names appear next to the message.

Right now the new messages are broadcasted to all clients. We need to attach the socket.io session ids
to each user account so that we can filter the broadcasts to certain clients.
'''

# TODO: Use live database instead
db = {
    'conversations': [
        {
            'id': 1,
            'participants': [ 1, 2 ],
        }
    ],
    'messages': [
        {
            'id': 1,
            'text': 'Hello',
            'sender': 1,
            'conversation_id': 1
        },
        {
            'id': 2,
            'text': 'Hi',
            'sender': 2,
            'conversation_id': 1
        }
    ],
    'users': [
        {
            'id': 7,
            'first_name': 'Alex',
            'last_name': 'Wohlbruck'
        },
        {
            'id': 2,
            'first_name': 'Jackson',
            'last_name': 'Sippe'
        }
    ]
}

# Helper methods to find values in the fake DB
def search(dict, key, value):
    for item in dict:
        if item.get(key) == value:
            return item

def search_many(dict, key, value):
    results = []
    for item in dict:
        if item.get(key) == value:
            results.append(item)
    return results

def populateUser(user):
    return search(db.get('users'), 'id', user)

def populateParticipants(convo):
    convo['participants'] = list(map(populateUser, convo.get('participants')))
    return convo

def populateMessage(message):
    message['sender'] = search(db.get('users'), 'id', message.get('sender'))
    return message

###################
###################


@bp.route('/conversations', methods=['GET'])
@login_required
def conversations():
    conversations = db.session.query(Conversation).all()

    # List conversations
    if request.method == 'GET':
        return jsonify({
            'conversations': [conversation.to_dict() for conversation in conversations]
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

        cid = int(conversation_id)
        
        # The last message id that was recieved by the client.
        # Return the most recent if not set
        last_id = request.args.get('last_id')

        # The amount of messages to return
        limit = request.args.get('limit')

        # TODO: Query the messages for a given last_id and limit
        messages = search_many(test_db.get('messages'), 'conversation_id', int(cid))

        return jsonify({
            'messages': list(map(populateMessage, messages))
        }) 

    # Send a message
    if request.method == 'POST':

        cid = int(conversation_id)
        
        return jsonify({
            'message': send_message(conversation_id, {
                'text': request.json.get('text')
            })
        })

# Send a message through socket.io
#! NOTE: It may be better to stick with rest for as much as we can.
#        POST /conversations/<conversation_id>/messages does the same thing as this,
#        however if it is noticably faster to use the socket connection, we can stick to using this.
@socketio.on('message:create')
def socket_send_message(data):
    send_message(
        data.get('conversation_id'),
        data.get('user_id'),
        data.get('message')
    )
    message = Message (
        sender_id=data.get('user_id'),
        body=data.get('message').get('text'),
    )
    db.session.add(message)
    db.session.commit()

def send_message(conversation_id, user_id, message):

    # TODO: Get user ID from database by querying for socket session id

    user = search(test_db.get('users'), 'id', user_id)

    new_message = {
        'id': randint(1, 10000),
        'conversation_id': conversation_id,
        'sender': user,
        'text': message.get('text')
    }

    test_db.get('messages').append(new_message)
    
    socketio.emit('message:create', {
        'message': new_message,
        'conversation_id': conversation_id
    })

    return new_message