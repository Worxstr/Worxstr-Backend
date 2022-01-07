from pyfcm import FCMNotification


class Push:
    push_service = None
    table = None
    db = None

    def __init__(self, server_key, db, table):
        self.push_service = FCMNotification(api_key=server_key)
        self.db = db
        self.table = table

    def send_notification(self, message_title, message_body, users):
        query = (
            self.db.session.query(self.table.registration_id)
            .filter(self.table.user_id.in_(users))
            .all()
        )
        registration_ids = []
        for i in query:
            registration_ids.append(i[0])

        result = self.push_service.notify_multiple_devices(
            registration_ids=registration_ids,
            message_title=message_title,
            message_body=message_body,
        )
        return result
