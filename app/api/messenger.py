"""
TODO:
I have implemented some basic messaging so far. You can send messages from
different user accounts, and the messages that other users have send appear on
the left, and your messages on the right

I mapped employeeone@worxstr.com to name Jackson Sippe and
managerone@worxstr.com to Alex Wohlbruck, so when logged in to those accounts,
the names appear next to the message

Right now the new messages are broadcasted to all clients. We need to attach
the socket.io session ids to each user account so that we can filter the
broadcasts to certain clients.
"""

from flask import abort, request
from flask_security import current_user, login_required

from app.models import Message, User, Conversation
from app.api import bp
from app import db, socketio

@socketio.on('connect')
def on_connect():
	# TODO: Attach the client session id to the user data in DB
	print("Client connected")

@bp.route('/conversations', methods=['GET', 'POST'])
@login_required
def conversations():
	# List conversations
	if request.method == 'GET':
		all_conversations = db.session.query(Conversation).all()
		user_conversations = []
		for i in all_conversations:
			for participant in i.participants:
				if int(current_user.get_id()) == participant.id:
					user_conversations.append(i.to_dict())
		return {'conversations': user_conversations}

	# POST request
	participants = [current_user]

	try:
		recipients = request.json['users']
	except KeyError as key:
		abort(400, f"Request attribute not found: {key}")

	for recipient_id in recipients:
		participants.append(
			db.session.query(User).filter(User.id==recipient_id).one()
		)

	new_conversation = Conversation(participants=participants)
	db.session.add(new_conversation)
	db.session.commit()

	return {"conversation": new_conversation.to_dict()}

@bp.route('/conversations/contacts', methods=['GET'])
@login_required
def contacts():
	org_contacts = db.session \
		.query(User) \
		.filter(User.organization_id==current_user.organization_id) \
		.all()
	return {'contacts': [contact.to_dict() for contact in org_contacts]}

@bp.route('/conversations/<conversation_id>', methods=['GET'])
@login_required
def conversation(conversation_id):
	# Get conversation data along with messages
	selected_conversation = db.session \
		.query(Conversation) \
		.filter(Conversation.id == conversation_id) \
		.one() \
		.to_dict()
	return {'conversation': selected_conversation}

@bp.route('/conversations/<conversation_id>/messages', methods=['GET', 'POST'])
@login_required
def messages(conversation_id):

	# List messages in a conversation
	if request.method == 'GET':
		# The last message id that was recieved by the client.
		# Return the most recent if not set
		# Currently unused
		# last_id = request.args.get('last_id')

		# The amount of messages to return
		# Currently unused
		# limit = request.args.get('limit')

		# TODO: Query the messages for a given last_id and limit
		conversation_messages = db.session \
			.query(Message) \
			.filter(Message.conversation_id == conversation_id) \
			.all()

		return {'messages': [message.to_dict() for message in conversation_messages]}

	# POST request: Send a message
	try:
		message_body = request.json['body']
	except KeyError as key:
		abort(400, f"Request attribute not found: {key}")

	return {
		'message': send_message(
			conversation_id,
			current_user.get_id(),
			{'body': message_body}
		)
	}

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

	socketio.emit(
		'message:create',
		{
			'message': socket_message,
			'conversation_id': conversation_id
		}
	)

	return socket_message
