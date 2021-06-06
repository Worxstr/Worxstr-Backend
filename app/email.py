from threading import Thread
import os

from flask import current_app
from flask_mail import Message

from app import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body, attachment=None):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if attachment != None:
        with current_app.open_resource(attachment) as fp:
            msg.attach(os.path.basename(attachment), "image/png", fp.read())
    Thread(
        target=send_async_email, args=(current_app._get_current_object(), msg)
    ).start()
