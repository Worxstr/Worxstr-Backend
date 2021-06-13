"""
Plumbing for scheduling functionality
"""
from app import db
from app.models import ScheduleShift, User


def add_shift(
    job_id, time_begin, time_end, site_location, employee_id, timecard_id=None
):
    """
    Instantiate a ScheduleShift and insert it into the database and return the instance.

    :param job_id: The job_id of the Shift.
    :param time_begin: The begin time of the Shift.
    :param time_end: The end time of the Shift.
    :param site_location: The site_location of the Shift.
    :param employee_id: The employee_id of the Shift.
    :param timecard_id: The timecard_id of the Shift. Defaults to None
    :return: The shift instance.
    """
    shift = ScheduleShift(
        job_id=job_id,
        time_begin=time_begin,
        time_end=time_end,
        site_location=site_location,
        employee_id=employee_id,
        timecard_id=timecard_id,
    )

    db.session.add(shift)
    db.session.commit()

    return shift


def get_shift_employee(shift):
    """
    Get the User that is assigned as "employee" on a shift.

    :param shift: The Shift object.
    :return: The user object.
    """
    return db.session.query(User).filter(User.id == shift.employee_id).one()
