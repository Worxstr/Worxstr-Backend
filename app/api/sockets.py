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

from app import socketio, db
from app.models import User, Sessions

##################################################
# Manages and links socket io user and session ids
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

    db.session.add(Sessions(user_id=user_id, session_id=session_id))
    db.session.commit()


def remove_session(session_id):
    db.session.query(Sessions).filter(Sessions.session_id == session_id).delete()
    db.session.commit()


def lookup_session_ids(user_id):
    return (
        db.session.query(Sessions.session_id).filter(Sessions.user_id == user_id).all()
    )


def lookup_user_id(session_id):
    return (
        db.session.query(Sessions.user_id)
        .filter(Sessions.session_id == session_id)
        .all()
    )


def emit_to_users(event_name, payload, user_ids):
    for user_id in user_ids:
        session_ids = lookup_session_ids(user_id)
        for session_id in session_ids:
            socketio.emit(event_name, payload, room=session_id)


######################################


def get_user_from_uniquifier(uniquifier):
    user = db.session.query(User).filter(User.fs_uniquifier == uniquifier).one_or_none()
    if user != None and not user.active:
        user = None
    return user


@socketio.on("connect")
@socketio.on("sign-in")
def sign_in(auth=None):
    print("socket.io client connected: " + request.sid)
    if auth != None:
        user = get_user_from_uniquifier(auth["fs_uniquifier"])
        if user != None:
            add_session(request.sid, user.id)


@socketio.on("disconnect")
@socketio.on("sign-out")
def sign_out():
    remove_session(request.sid)
