"""
TODO:
I have implemented some basic messaging so far. You can send messages from
different user accounts, and the messages that other users have send appear on
the left, and your messages on the right

I mapped contractorone@worxstr.com to name Jackson Sippe and
managerone@worxstr.com to Alex Wohlbruck, so when logged in to those accounts,
the names appear next to the message

Right now the new messages are broadcasted to all clients. We need to attach
the socket.io session ids to each user account so that we can filter the
broadcasts to certain clients.
"""

from flask import request
from flask_security import current_user, login_required
from flask_security.core import _security

from app import db, socketio
from app.api import bp
from app.models import Message, User, Conversation
from app.utils import get_request_arg, get_request_json


##################################################
# Manages and links socket io user and session ids
# TODO: Move this to a separate module
######################################

# Store all user ids associated per session
by_session_id = {
    # "A-Q9HUwePySd5HNoAAAC": "123"
}
# Store all sessions associated with a user id
by_user_id = {
    # "123": ["A-Q9HUwePySd5HNoAAAC"]
}

def add_session(session_id, user_id):

    # Add user id to by_session_id dict
    by_session_id[session_id] = user_id

    # Add session id to by_user_id dict
    if user_id in by_user_id:
        by_user_id[user_id].append(session_id)
    else:
        by_user_id[user_id] = [session_id]


def remove_session(session_id):
    
    if session_id in by_session_id:
        
        # Delete session_id from array in by_user_id dict
        user_id = by_session_id[session_id]
        by_user_id[user_id].remove(session_id)
        if len(by_user_id[user_id]) == 0:
            del by_user_id[user_id]
        
        # Delete user id from by_session_id dict
        del by_session_id[session_id]

def lookup_session_ids(user_id):
    return by_user_id.get(user_id, [])

def lookup_user_id(session_id):
    return by_session_id.get(session_id, None)

def emit_to_users(event_name, payload, user_ids):
    for user_id in user_ids:
        session_ids = lookup_session_ids(user_id)
        for session_id in session_ids:
            socketio.emit(event_name, payload, room=session_id)

######################################


def get_user_from_token(token):
    try:
        data = _security.remember_token_serializer.loads(
            token, max_age=_security.token_max_age
        )
        uniquifier_index = 0 if len(data) == 1 else 2

        if hasattr(_security.datastore.user_model, "fs_token_uniquifier"):
            user = _security.datastore.find_user(
                fs_token_uniquifier=data[uniquifier_index]
            )
            print("user token_uniqifier", user)
        else:
            user = _security.datastore.find_user(fs_uniquifier=data[uniquifier_index])
            print("user uniquifier", user)

        if not user.active:
            user = None

    except Exception:
        user = None

    if user and user.verify_auth_token(data):
        return user

    # User not found
    return _security.login_manager.anonymous_user()

@socketio.on("connect")
@login_required
def on_connect():
    print("SocketIO client connected")
    print("SocketIO Session ID:", request.sid)
    print("\n\n")
    print(request.headers)
    print("\n\n")


@socketio.on("test")
@login_required
def test(arg):
    print(current_user.id)
    print(arg)

@socketio.on("disconnect")
def on_disconnect():
    remove_session(request.sid)

@socketio.on("sign-in")
def sign_in(auth_token):
    user = get_user_from_token(auth_token)
    add_session(request.sid, user.id)
    print(by_user_id)

@socketio.on("sign-out")
def sign_out(auth_token):
    remove_session(request.sid)


@bp.route("/conversations", methods=["GET"])
@login_required
def get_conversations():
    """
    Fetch all conversations for the current user
    ---
    responses:
        200:
            description: List of conversations for the current user.
            schema:
                type: object
                properties:
                    conversations:
                        type: array
                        items:
                            $ref: '#/definitions/Conversation'
    """
    all_conversations = db.session.query(Conversation).all()
    user_conversations = []
    # TODO: This can be a single comprehension without a nested loop
    for i in all_conversations:
        for participant in i.participants:
            if int(current_user.id) == participant.id:
                user_conversations.append(i.to_dict())
    return {"conversations": user_conversations}


@bp.route("/conversations", methods=["POST"])
@login_required
def create_conversation():
    """
    Create a new conversation between the current user and a list of other users.
    ---
    parameters:
        - name: users
          description: "List of IDs for the users to be including in the conversation."
          in: body
          type: array
          items:
              type: string
          required: true
    definitions:
        Conversation:
            type: object
            properties:
                id:
                    type: integer
                participants:
                    type: array
                    items:
                        ref: '/definitions/User'
                messages:
                    type: array
                    items:
                        ref: '/definitions/Message'
    responses:
        200:
            description: The new conversation.
            schema:
                type: object
                properties:
                    conversation:
                        type: array
                        items:
                            $ref: '#/definitions/Conversation'
    """
    participants = [current_user]

    recipients = get_request_json(request, "users")

    for recipient_id in recipients:
        participants.append(
            db.session.query(User).filter(User.id == recipient_id).one()
        )

    new_conversation = Conversation(participants=participants)
    db.session.add(new_conversation)
    db.session.commit()

    return {"conversation": new_conversation.to_dict()}


@bp.route("/conversations/contacts", methods=["GET"])
@login_required
def contacts():
    """
    List all users in the current organization.
    ---
    responses:
        200:
            description: The new conversation.
            schema:
                type: object
                properties:
                    contacts:
                        type: array
                        items:
                            $ref: '#/definitions/User'
    """
    # TODO: Implement paging here
    org_contacts = (
        db.session.query(User)
        .filter(
            User.organization_id == current_user.organization_id, User.active == True
        )
        .all()
    )
    return {"contacts": [contact.to_dict() for contact in org_contacts]}


@bp.route("/conversations/<conversation_id>", methods=["GET"])
@login_required
def conversation(conversation_id):
    """
    Get a conversation by ID.
    ---
    parameters:
        - name: conversation_id
          description: ID of the requested conversation.
          in: path
          type: string
          required: true
    responses:
        200:
            description: The requested conversation.
            schema:
                type: object
                properties:
                    conversation:
                        $ref: '#/definitions/Conversation'
    """
    # TODO: make sure the user has access to the requested conversation
    selected_conversation = (
        db.session.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .one()
        .to_dict()
    )
    return {"conversation": selected_conversation}


@bp.route("/conversations/<conversation_id>/messages", methods=["GET"])
@login_required
def get_messages(conversation_id):
    """
    Get messages in a conversation.
    ---
    parameters:
        - name: conversation_id
          description: ID of the conversation which contains the desired messages.
          in: path
          type: string
          required: true
    definitions:
        Message:
            type: object
            properties:
                id:
                    type: integer
                sender_id:
                    type: integer
                body:
                    type: string
                timestamp:
                    type: string
                    format: date-time
                conversation_id:
                    type: integer
    responses:
        200:
            description: The requested conversation.
            schema:
                type: object
                properties:
                    messages:
                        type: array
                        items:
                            $ref: '#/definitions/Message'
    """
    # The last message id that was recieved by the client.
    # Return the most recent if not set
    # Currently unused
    # last_id = request.args.get('last_id')

    # The amount of messages to return
    # Currently unused
    # limit = request.args.get('limit')

    # TODO: Query the messages for a given last_id and limit
    # TODO: Implement paging here
    conversation_messages = (
        db.session.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .all()
    )

    return {"messages": [message.to_dict() for message in conversation_messages]}


@bp.route("/conversations/<conversation_id>/messages", methods=["POST"])
@login_required
def create_messages(conversation_id):
    """
    Add a new message to a conversaion.
    ---
    parameters:
        - name: conversation_id
          description: The ID of the conversation to add the new message too.
          in: path
          type: string
          required: true
    responses:
        200:
            description: The requested conversation.
            schema:
                type: object
                properties:
                    message:
                        $ref: '#/definitions/Message'
    """
    message_body = get_request_json(request, "body")

    return {
        "message": send_message(
            conversation_id, current_user.id, {"body": message_body}
        )
    }


def send_message(conversation_id, user_id, message):
    # TODO: Get user ID from database by querying for socket session id
    db_message = Message(
        sender_id=user_id, body=message.get("body"), conversation_id=conversation_id
    )
    db.session.add(db_message)
    db.session.commit()

    socket_message = {
        "id": db_message.id,
        "sender_id": user_id,
        "conversation_id": conversation_id,
        "body": message.get("body"),
    }

    socketio.emit(
        "message:create",
        {"message": socket_message, "conversation_id": conversation_id},
    )

    return socket_message
