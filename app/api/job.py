from datetime import datetime
from random import randint
import os

from flask import abort, request, render_template, current_app
from flask_security import login_required, current_user, roles_required, roles_accepted
from sqlalchemy import or_, not_
import pyqrcode
from app.api.sockets import emit_to_users

from app import db
from app.api import bp
from app.email import send_email
from app.models import ContractorInfo, Job, User, ScheduleShift, TimeClock, Role
from app.utils import get_request_arg, get_request_json, OK_RESPONSE


def get_manager_user_ids(organization_id):
    # Get the ids of managers within the current organization
    return [
        r[0]
        for r in db.session.query(User.id)
        .filter(
            User.organization_id == organization_id,
            User.roles.any(
                Role.name.in_(["contractor_manager", "organization_manager"])
            ),
        )
        .all()
    ]


@bp.route("/jobs", methods=["GET"])
@login_required
@roles_accepted("contractor_manager", "organization_manager")
def list_jobs():
    """
    Get a list of registered jobs and the available managers for the jobs.
    ---
    definitions:
        Job:
            type: object
            properties:
                id:
                    type: integer
                name:
                    type: string
                organization_id:
                    type: integer
                contractor_manager_id:
                    type: integer
                organization_manager_id:
                    type: integer
                address:
                    type: string
                city:
                    type: string
                state:
                    type: string
                zip_code:
                    type: string
                country:
                    type: string
                consultant_name:
                    type: string
                consultant_phone:
                    type: string
                consultant_email:
                    type: string
                consultant_code:
                    type: string
                longitude:
                    type: number
                latitude:
                    type: number
                active:
                    type: boolean
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
                        contractor_managers:
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
        "managers": get_managers(),
    }

    # direct_ids = []
    # direct_jobs = (
    #     db.session.query(Job)
    #     .filter(
    #         Job.contractor_manager_id == current_user.id
    #         or Job.organization_manager_id == current_user.id,
    #         Job.active,
    #     )
    #     .all()
    # )
    # for direct_job in direct_jobs:
    #     job = direct_job.to_dict()
    #     result["jobs"].append(job)
    #     direct_ids.append(direct_job.id)

    # lower_managers = get_lower_managers(current_user.id)
    # indirect_jobs = (
    #     db.session.query(Job)
    #     .filter(
    #         not_(Job.id.in_(direct_ids)),
    #         or_(
    #             Job.organization_manager_id.in_(lower_managers),
    #             Job.contractor_manager_id.in_(lower_managers),
    #         ),
    #         Job.active,
    #     )
    #     .all()
    # )

    # for indirect_job in indirect_jobs:
    #     job = indirect_job.to_dict()
    #     result["jobs"].append(job)
    jobs = (
        db.session.query(Job)
        .filter(
            Job.organization_id == current_user.organization_id,
            Job.active,
        )
        .all()
    )
    for job in jobs:
        result["jobs"].append(job.to_dict())
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
        - name: contractor_manager_id
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
        - name: color
          in: body
          type: string
          format: hex
          required: true
        - name: radius
          in: body
          type: int
          required: true
    responses:
        200:
            description: The newly created job.
            schema:
                $ref: '#/definitions/Job'
    """
    consultant_phone_raw = get_request_json(request, "consultant_phone")
    consultant_phone = (
        consultant_phone_raw["areaCode"] + consultant_phone_raw["phoneNumber"]
    )
    job = Job(
        name=get_request_json(request, "name"),
        organization_id=current_user.organization_id,
        contractor_manager_id=get_request_json(request, "contractor_manager_id"),
        organization_manager_id=get_request_json(request, "organization_manager_id"),
        address=get_request_json(request, "address"),
        city=get_request_json(request, "city"),
        state=get_request_json(request, "state"),
        country=get_request_json(request, "country"),
        zip_code=get_request_json(request, "zip_code"),
        longitude=get_request_json(request, "longitude"),
        latitude=get_request_json(request, "latitude"),
        consultant_name=get_request_json(request, "consultant_name"),
        consultant_phone=consultant_phone,
        consultant_email=get_request_json(request, "consultant_email"),
        consultant_code=str(randint(000000, 999999)),
        color=get_request_json(request, "color"),
        radius=get_request_json(request, "radius"),
    )
    db.session.add(job)
    db.session.commit()

    send_consultant_code(job.id)

    response = job.to_dict()
    emit_to_users(
        "ADD_JOB", response, get_manager_user_ids(current_user.organization_id)
    )
    return response


@bp.route("/jobs/<job_id>", methods=["GET"])
@login_required
@roles_accepted("contractor_manager", "organization_manager")
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
        shift["contractor"] = (
            db.session.query(User)
            .filter(User.id == shift["contractor_id"])
            .one_or_none()
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
        contractor = (
            db.session.query(User)
            .filter(User.id == shift["contractor_id"])
            .one_or_none()
        )
        if contractor == None:
            shift["contractor"] = None
        else:
            shift["contractor"] = contractor.to_dict()
        shifts.append(shift)

    job["shifts"] = shifts
    job["managers"] = get_managers()
    job["contractors"] = []
    contractors = db.session.query(User).filter(
        User.organization_id == current_user.organization_id,
        User.active == True,
    )
    for contractor in contractors:
        if contractor.has_role("contractor"):
            job["contractors"].append(contractor.to_dict())

    job["contractor_manager"] = (
        db.session.query(User)
        .filter(User.id == job["contractor_manager_id"])
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
@roles_accepted("contractor_manager", "organization_manager")
@bp.route("/jobs/managers", methods=["GET"])
def get_managers():
    """
    Get list of managers.
    Data is separated into lists of who manages contractors and the organization.
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
                        "List of with the role
                        'organization_manager', including the
                        calling user, if applicable."
                contractor_managers:
                    type: array
                    items:
                        $ref '#/definitions/User'
                    description:
                        "List of with the role
                        'contractor_manager', including the
                        calling user, if applicable."
    responses:
        200:
            description: Lists of managers
            schema:
                $ref: '#/definitions/ManagersList'
    """
    organization_managers = []
    contractor_managers = []

    users = (
        db.session.query(User)
        .filter(
            User.organization_id == current_user.organization_id, User.active == True
        )
        .all()
    )

    for user in users:
        if user.has_role("contractor_manager"):
            contractor_managers.append(user.to_dict())
        if user.has_role("organization_manager"):
            organization_managers.append(user.to_dict())

    return {
        "organization_managers": organization_managers,
        "contractor_managers": contractor_managers,
    }


def get_lower_managers(manager_id):
    users = (
        db.session.query(User)
        .filter(
            User.manager_id == manager_id,
            User.organization_id == current_user.organization_id,
            User.active == True,
        )
        .all()
    )

    lower_managers = []
    for user in users:
        if user.has_role("contractor_manager") or user.has_role("organization_manager"):
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

    consultant_phone_raw = get_request_json(request, "consultant_phone")
    consultant_phone = (
        consultant_phone_raw["areaCode"] + consultant_phone_raw["phoneNumber"]
    )

    try:
        db.session.query(Job).filter(Job.id == job_id).update(
            {
                Job.name: get_request_json(request, "name"),
                Job.contractor_manager_id: get_request_json(
                    request, "contractor_manager_id"
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
                Job.consultant_phone: consultant_phone,
                Job.consultant_email: get_request_json(request, "consultant_email"),
                Job.color: get_request_json(request, "color"),
                Job.radius: get_request_json(request, "radius"),
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

    response = job.to_dict()
    emit_to_users(
        "ADD_JOB", response, get_manager_user_ids(current_user.organization_id)
    )
    return response


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

    emit_to_users(
        "REMOVE_JOB", int(job_id), get_manager_user_ids(current_user.organization_id)
    )

    return OK_RESPONSE
