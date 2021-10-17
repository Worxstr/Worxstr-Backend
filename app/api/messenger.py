from flask import request
from flask_security import current_user, login_required

from app import db, socketio
from app.api import bp
from app.models import Message, User, Conversation
from app.utils import get_request_arg, get_request_json
from app.api.sockets import emit_to_users


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
    recipient_ids = [current_user.id]
    for recipient_id in recipients:
        recipient_ids.append(int(recipient_id))
        participants.append(
            db.session.query(User).filter(User.id == recipient_id).one()
        )

    new_conversation = Conversation(participants=participants)
    db.session.add(new_conversation)
    db.session.commit()

    emit_to_users("ADD_CONVERSATION", new_conversation.to_dict(), participants)

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
    conversation = db.session.query(Conversation).get(conversation_id).to_dict()

    new_message = Message(
        sender_id=user_id, body=message.get("body"), conversation_id=conversation_id
    )
    db.session.add(new_message)
    db.session.commit()

    participant_ids = [c["id"] for c in conversation["participants"]]

    emit_to_users("ADD_MESSAGE", new_message.to_dict(), participant_ids)

    return new_message.to_dict()
