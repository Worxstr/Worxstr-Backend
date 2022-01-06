from pyfcm import FCMNotification
from app.models import User

class Push:
    push_service = None

    def __init__(self, server_key):
        self.push_service = FCMNotification(api_key=server_key)
    
    def send_notification(self, message_title, message_body, users):
        if type(users) is list and len(users) == 1:
            registration_id = db.session.query(User.registration_id).filter_by(User.id == users[0]).one()[0]
            result = self.push_service.notify_single_device(registration_id=registration_id, message_title=message_title, message_body=message_body)
            return result
        elif type(users) is list:
            registration_ids = db.session.query(User.registration_id).filter_by(User.id.in_(tuple(users))).all()
            result=self.push_service.notify_multiple_devices(registration_ids=registration_ids, message_title=message_title, message_body=message_body)
            return result
