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

from flask_security.core import _security
from flask import request

from app import socketio

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
# @login_required
def on_connect():
    print("SocketIO client connected")
    print("SocketIO Session ID:", request.sid)
    print("\n\n")
    print(request.headers)
    print("\n\n")

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
