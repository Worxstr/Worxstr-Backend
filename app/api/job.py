from datetime import datetime
from random import randint
import os

from flask import abort, request, render_template, current_app
from flask_security import login_required, current_user, roles_required, roles_accepted
from sqlalchemy import or_, not_
import pyqrcode

from app import db
from app.api import bp
from app.email import send_email
from app.models import EmployeeInfo, Job, User, ScheduleShift, TimeClock
from app.utils import get_request_arg, get_request_json


@bp.route("/jobs", methods=["GET"])
@login_required
@roles_accepted("employee_manager", "organization_manager")
def list_jobs():
    """
    Get a list of registered jobs and the available managers for the jobs.
    ---
    definitions:
        JobsAndManagers:
            type: object
            properties:
                jobs:
                    type: array
                    items:
                        $ref '#/definitions/Job'
                    description: List of jobs.
                managers:
                    type: object
                    description: Managers that can be assigned to returned jobs.
                    properties:
                        organization_managers:
                            type: array
                            items:
                                $ref: '#/definitions/User'
                        employee_managers:
                            type: array
                            items:
                                $ref: '#/definitions/User'
    responses:
        200:
            description: A list of jobs
            schema:
                $ref: '#/definitions/JobsAndManagers'
    """
    result = {
        "jobs": [],
        "managers": get_managers(current_user.manager_id or current_user.get_id()),
    }

    direct_ids = []
    direct_jobs = (
        db.session.query(Job)
        .filter(Job.employee_manager_id == current_user.get_id(), Job.active)
        .all()
    )
    for direct_job in direct_jobs:
        job = direct_job.to_dict()
        job["direct"] = True
        result["jobs"].append(job)
        direct_ids.append(direct_job.id)

    lower_managers = get_lower_managers(current_user.get_id())
    indirect_jobs = (
        db.session.query(Job)
        .filter(
            not_(Job.id.in_(direct_ids)),
            or_(
                Job.organization_manager_id.in_(lower_managers),
                Job.employee_manager_id.in_(lower_managers),
            ),
            Job.active,
        )
        .all()
    )

    for indirect_job in indirect_jobs:
        job = indirect_job.to_dict()
        job["direct"] = False
        result["jobs"].append(job)

    return result


@bp.route("/jobs", methods=["POST"])
@login_required
@roles_required("organization_manager")
def add_job():
    """
    Create a new job entry.
    ---
    parameters:
        - name: name
          in: body
          type: string
          required: true
        - name: employee_manager_id
          in: body
          type: integer
          required: true
        - name: organization_manager_id
          in: body
          type: integer
          required: true
        - name: address
          in: body
          type: string
          required: true
        - name: city
          in: body
          type: string
          required: true
        - name: state
          in: body
          type: string
          required: true
        - name: country
          in: body
          type: string
          required: true
        - name: zip_code
          in: body
          type: string
          required: true
        - name: longitude
          in: body
          type: string
          required: true
        - name: latitude
          in: body
          type: string
          required: true
        - name: consultant_name
          in: body
          type: string
          required: true
        - name: consultant_phone
          in: body
          type: string
          required: true
        - name: consultant_email
          in: body
          type: string
          format: email
          required: true
    responses:
        200:
            description: The newly created job.
            schema:
                $ref: '#/definitions/Job'
    """
    job = Job(
        name=get_request_json(request, "name"),
        organization_id=current_user.organization_id,
        employee_manager_id=get_request_json(request, "employee_manager_id"),
        organization_manager_id=get_request_json(request, "organization_manager_id"),
        address=get_request_json(request, "address"),
        city=get_request_json(request, "city"),
        state=get_request_json(request, "state"),
        country=get_request_json(request, "country"),
        zip_code=get_request_json(request, "zip_code"),
        longitude=get_request_json(request, "longitude"),
        latitude=get_request_json(request, "latitude"),
        consultant_name=get_request_json(request, "consultant_name"),
        consultant_phone=get_request_json(request, "consultant_phone"),
        consultant_email=get_request_json(request, "consultant_email"),
        consultant_code=str(randint(000000, 999999)),
    )

    db.session.add(job)
    db.session.commit()

    send_consultant_code(job.id)

    return {"job": job.to_dict()}


@bp.route("/jobs/<job_id>", methods=["GET"])
@login_required
@roles_accepted("employee_manager", "organization_manager")
def job_detail(job_id):
    """
    Get details about a job, by ID.
    ---
    parameters:
        - name: Job ID
          in: path
          type: string
          required: true
    responses:
        200:
            description: Job details.
    """
    job = db.session.query(Job).filter(Job.id == job_id).one().to_dict()
    # Collect all the current and future shifts for a job
    scheduled_shifts = (
        db.session.query(ScheduleShift)
        .filter(
            ScheduleShift.job_id == job["id"],
            ScheduleShift.time_begin > datetime.utcnow(),
        )
        .all()
    )
    active_shifts = (
        db.session.query(ScheduleShift)
        .filter(
            ScheduleShift.job_id == job["id"],
            ScheduleShift.time_begin <= datetime.utcnow(),
            ScheduleShift.time_end >= datetime.utcnow(),
        )
        .all()
    )

    shifts = []
    # Add all scheduled shifts
    for shift in [s.to_dict() for s in scheduled_shifts]:
        shift["employee"] = (
            db.session.query(User)
            .filter(User.id == shift["employee_id"])
            .one()
            .to_dict()
        )
        shifts.append(shift)

    # Add all active shifts
    for shift in [s.to_dict() for s in active_shifts]:
        shift["active"] = True
        timeclocks = (
            db.session.query(TimeClock)
            .filter(TimeClock.timecard_id == shift["timecard_id"])
            .order_by(TimeClock.time.desc())
            .all()
        )
        shift["timeclock_actions"] = [timeclock.to_dict() for timeclock in timeclocks]
        shift["employee"] = (
            db.session.query(User)
            .filter(User.id == shift["employee_id"])
            .one()
            .to_dict()
        )
        shifts.append(shift)

    job["shifts"] = shifts
    job["managers"] = get_managers(current_user.manager_id or current_user.get_id())
    job["employees"] = []
    employees = db.session.query(User).filter(User.manager_id == current_user.id)

    for employee in [e.to_dict() for e in employees if e.has_role("employee")]:
        employee["employee_info"] = (
            db.session.query(EmployeeInfo)
            .filter(EmployeeInfo.id == employee["id"])
            .one()
            .to_dict()
        )
        job["employees"].append(employee)

    job["employee_manager"] = (
        db.session.query(User)
        .filter(User.id == job["employee_manager_id"])
        .one()
        .to_dict()
    )
    job["organization_manager"] = (
        db.session.query(User)
        .filter(User.id == job["organization_manager_id"])
        .one()
        .to_dict()
    )
    return {"job": job}


@login_required
@roles_accepted("employee_manager", "organization_manager")
@bp.route("/jobs/managers", methods=["GET"])
def get_managers(manager_id=None):
    """
    Get list of subordinate managers, including the calling manager.
    Data is separated into lists of who manages employees and the organization.
    ---
    parameters:
        - name: Manager ID
          in: body
          type: string
          required: true
    definitions:
        ManagersList:
            type: object
            properties:
                organization_managers:
                    type: array
                    items:
                        $ref '#/definitions/User'
                    description:
                        "List of sub-manangers with the role
                        'organization_manager', including the
                        calling user, if applicable."
                employee_managers:
                    type: array
                    items:
                        $ref '#/definitions/User'
                    description:
                        "List of sub-manangers with the role
                        'employee_manager', including the
                        calling user, if applicable."
    responses:
        200:
            description: Lists of managers
            schema:
                $ref: '#/definitions/ManagersList'
    """
    if not manager_id:
        manager_id = get_request_arg(request, "manager_id")

    managers = get_lower_managers(manager_id)
    result = {"organization_managers": [], "employee_managers": []}

    for manager in managers:
        user = db.session.query(User).filter(User.id == manager).one()
        if user.has_role("organization_manager"):
            result["organization_managers"].append(user.to_dict())
        if user.has_role("employee_manager"):
            result["employee_managers"].append(user.to_dict())

    if current_user.has_role("organization_manager"):
        result["organization_managers"].append(current_user.to_dict())
    if current_user.has_role("employee_manager"):
        result["employee_managers"].append(current_user.to_dict())

    return result


def get_lower_managers(manager_id):
    users = (
        db.session.query(User)
        .filter(
            User.manager_id == manager_id,
            User.organization_id == current_user.organization_id,
        )
        .all()
    )

    lower_managers = []
    for user in users:
        if user.has_role("employee_manager") or user.has_role("organization_manager"):
            lower_managers.append(user.id)
            for i in get_lower_managers(user.id):
                # TODO: a recursive database call could be a _very_ bad idea
                lower_managers.append(i)

    return lower_managers


@bp.route("/jobs/<job_id>", methods=["PUT"])
@login_required
@roles_required("organization_manager")
def edit_job(job_id):
    """
    Update a job object.
    ---
    parameters:
        - name: Job ID
          in: path
          type: string
          required: true
    definitions:
        ReturnJob:
            type: object
            properties:
                job:
                    $ref: '#/definitions/User'
    responses:
        200:
            description: Updated job.
            schema:
                $ref: '#/definitions/ReturnJob'
    """
    job = db.session.query(Job).filter(Job.id == job_id).one()

    original_email = job.consultant_email
    original_code = job.consultant_code

    try:
        db.session.query(Job).filter(Job.id == job_id).update(
            {
                Job.name: get_request_json(request, "name"),
                Job.employee_manager_id: get_request_json(
                    request, "employee_manager_id"
                ),
                Job.organization_manager_id: get_request_json(
                    request, "organization_manager_id"
                ),
                Job.address: get_request_json(request, "address"),
                Job.city: get_request_json(request, "city"),
                Job.state: get_request_json(request, "state"),
                Job.zip_code: get_request_json(request, "zip_code"),
                Job.longitude: get_request_json(request, "longitude"),
                Job.latitude: get_request_json(request, "latitude"),
                Job.consultant_name: get_request_json(request, "consultant_name"),
                Job.consultant_phone: get_request_json(request, "consultant_phone"),
                Job.consultant_email: get_request_json(request, "consultant_email"),
            }
        )

        if get_request_json(request, "generateNewCode", optional=True):
            db.session.query(Job).filter(Job.id == job_id).update(
                {
                    # TODO: This should probably be unique
                    Job.consultant_code: str(randint(000000, 999999))
                }
            )

        db.session.commit()
    except Exception:
        abort(500)

    if job.consultant_email != original_email or job.consultant_code != original_code:
        send_consultant_code(job.id)

    return {"job": job.to_dict()}


def send_consultant_code(job_id):
    job = db.session.query(Job).filter(Job.id == job_id).one()
    url = pyqrcode.create(job.consultant_code)
    if not os.path.exists("codes"):
        os.makedirs("codes")
    url.png("codes/qr_code.png", scale=6)

    send_email(
        "[Worxstr] Consultant Code for " + job.name,
        sender=current_app.config["ADMINS"][0],
        recipients=[job.consultant_email],
        text_body=render_template(
            "email/consultant_code.txt",
            user=job.consultant_name,
            job=job.name,
            code=job.consultant_code,
        ),
        html_body=render_template(
            "email/consultant_code.html",
            user=job.consultant_name,
            job=job.name,
            code=job.consultant_code,
        ),
        attachment="../codes/qr_code.png",
    )


@bp.route("/jobs/<job_id>/close", methods=["PUT"])
@login_required
@roles_required("organization_manager")
def close_job(job_id):
    """Marks a given job inactive
    ---
    parameters:
        - name: job_id
          in: url
          type: int
          required: true
    responses:
        200:
            description: The job that was closed
            schema:
                $ref: '#/definitions/Job'
    """
    db.session.query(Job).filter(Job.id == job_id).update({Job.active: False})
    db.session.commit()
    return OK_RESPONSE
