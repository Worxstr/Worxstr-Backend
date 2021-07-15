"""
Plumbing for User functionality.
"""
from app import db
from app.models import ScheduleShift, User


def get_users_list(user_ids):
    """
    Get a list of users from their list of IDs.

    :param user_ids: List of user IDs.
    :return: List of User objects.
    """
    return db.session.query(User).filter(User.id.in_(user_ids)).all()
