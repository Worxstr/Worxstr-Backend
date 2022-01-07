"""
Plumbing for scheduling functionality
"""
from app import db
from app.models import ScheduleShift, User


def add_shift(
    job_id,
    time_begin,
    time_end,
    site_location,
    contractor_id,
    timecard_id=None,
    notes=None,
):
    """
    Instantiate a ScheduleShift and insert it into the database and return the instance.

    :param job_id: The job_id of the Shift.
    :param time_begin: The begin time of the Shift.
    :param time_end: The end time of the Shift.
    :param site_location: The site_location of the Shift.
    :param contractor_id: The contractor_id of the Shift.
    :param timecard_id: The timecard_id of the Shift. Defaults to None
    :return: The shift instance.
    """
    shift = ScheduleShift(
        job_id=job_id,
        time_begin=time_begin,
        time_end=time_end,
        site_location=site_location,
        contractor_id=contractor_id,
        timecard_id=timecard_id,
        notes=notes,
    )

    db.session.add(shift)
    db.session.commit()

    return shift


def get_shift_contractor(shift):
    """
    Get the User that is assigned as "contractor" on a shift.

    :param shift: The Shift object.
    :return: The user object.
    """
    return db.session.query(User).filter(User.id == shift.contractor_id).one()
