import random
import string
import datetime

from random import randint

from flask import current_app, request, render_template
from flask_security import (
    hash_password,
    current_user,
    login_required,
    roles_required,
    roles_accepted,
)
from sqlalchemy.sql.operators import op

from app import db, user_datastore, geolocator, payments
from app.api import bp
from app.email import send_email
from app.models import (
    ManagerInfo,
    PushRegistration,
    User,
    ContractorInfo,
    Organization,
    Role,
    UserLocation,
)
from app.utils import get_request_arg, get_request_json, OK_RESPONSE
from app.api.sockets import emit_to_users
from app import payments
import pytz


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


@bp.route("/users", methods=["GET"])
@login_required
@roles_required("organization_manager")
def list_users():
    """
    Returns list of registered users
    ---
    responses:
        200:
            description: A list of users
            schema:
                type: array
                items:
                    $ref: '#/definitions/User'
    """
    result = (
        db.session.query(User)
        .filter(
            User.organization_id == current_user.organization_id, User.active == True
        )
        .all()
    )
    return {"users": [x.to_dict() for x in result]}


@bp.route("/users/reset-password", methods=["PUT"])
@login_required
def reset_password():
    """
    Reset the logged-in user's password
    ---
    responses:
        200:
            description: Password reset successfully
    """
    new_password = get_request_json(request, "password")

    db.session.query(User).filter(User.id == current_user.id).update(
        {User.password: hash_password(new_password)}
    )
    db.session.commit()
    return OK_RESPONSE


@bp.route("/users/add-manager", methods=["POST"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def add_manager():
    """
    Creates a new manager user
    ---
    responses:
        200:
            description: The created manager user
            schema:
                $ref: '#/definitions/User'
    """
    first_name = get_request_json(request, "first_name")
    last_name = get_request_json(request, "last_name")
    email = get_request_json(request, "email")
    phone_raw = get_request_json(request, "phone")
    phone = phone_raw["areaCode"] + phone_raw["phoneNumber"]
    roles = get_request_json(request, "roles")
    manager_id = get_request_json(request, "manager_id")

    password = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    confirmed_at = datetime.datetime.utcnow()
    organization_id = current_user.organization_id
    role_names = []
    for role in roles:
        role_names.append(role["name"])

    manager = user_datastore.create_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        roles=role_names,
        manager_id=manager_id,
        organization_id=organization_id,
        confirmed_at=confirmed_at,
        password=hash_password(password),
    )
    db.session.commit()

    manager_reference = ManagerInfo(
        id=manager.id, reference_number=manager_reference_generator()
    )
    db.session.add(manager_reference)
    db.session.commit()

    organization_name = (
        db.session.query(Organization.name)
        .filter(Organization.id == organization_id)
        .one()[0]
    )

    send_email(
        "[Worxstr] Welcome!",
        sender=current_app.config["ADMINS"][0],
        recipients=[email],
        text_body=render_template(
            "email/temp_password.txt",
            user=first_name,
            organization=organization_name,
            password=password,
        ),
        html_body=render_template(
            "email/temp_password.html",
            user=first_name,
            organization=organization_name,
            password=password,
        ),
    )
    result = manager.to_dict()
    user_ids = get_manager_user_ids(current_user.organization_id)
    emit_to_users("ADD_USER", result, user_ids)
    emit_to_users("ADD_WORKFORCE_MEMBER", manager.id, user_ids)
    return result


def manager_reference_generator():
    """
    Returns the first random number between min_ and max_ which is not already
    present in the database.
    """
    min_ = 10000
    max_ = 1000000000
    rand = str(randint(min_, max_))

    # TODO: Generate a unique number without querying the databse in a while loop
    while (
        db.session.query(ManagerInfo)
        .filter(ManagerInfo.reference_number == rand)
        .limit(1)
        .first()
        is not None
    ):

        rand = str(randint(min_, max_))

    return rand


@bp.route("/users/check-email/<email>", methods=["GET"])
def check_email(email):
    """
    Returns if an email does not yet exist in the database
    ---
    parameters:
        - name: email
          in: path
          type: string
          required: true
    responses:
        200:
            description: True or false, if the email is unused or used, respectively
            schema:
                $ref: '#/definitions/User'
    """
    account = db.session.query(User.id).filter(User.email == email).one_or_none()
    return {"success": account is None}, 200


@bp.route("/users/<id>", methods=["DELETE"])
@login_required
@roles_accepted("organization_manager")
def deactivate_manager(id):
    db.session.query(User).filter(
        User.id == id, User.organization_id == current_user.organization_id
    ).update({User.active: False})
    db.session.commit()

    user_ids = get_manager_user_ids(current_user.organization_id)

    emit_to_users("REMOVE_USER", int(id), user_ids)

    return OK_RESPONSE


@bp.route("/users/<id>", methods=["GET"])
@login_required
@roles_accepted("contractor_manager", "organization_manager")
def get_user(id):
    """Returns a user by their ID
    ---
    parameters:
        - name: id
          in: path
          type: number
          required: true
    definitions:
        User:
            type: object
            properties:
                first:
                    type: string
                    example: Jackson
                last:
                    type: string
                    example: Sippe
    responses:
        200:
            description: The specified user
            schema:
                $ref: '#/definitions/User'
    """
    user = (
        db.session.query(User).filter(User.id == id, User.active == True).one_or_none()
    )
    result = user
    if user:
        result = user.to_dict()
        if user.has_role("contractor"):
            result["contractor_info"] = (
                db.session.query(ContractorInfo)
                .filter(ContractorInfo.id == id)
                .one()
                .to_dict()
            )
        else:
            result["manager_info"] = (
                db.session.query(ManagerInfo)
                .filter(ManagerInfo.id == id)
                .one()
                .to_dict()
            )
    return result, 200


@bp.route("/users/me", methods=["GET"])
@login_required
def get_authenticated_user():
    """
    Returns the currently authenticated user
    """
    authenticated_user = current_user.to_dict()
    authenticated_user["roles"] = [x.to_dict() for x in current_user.roles]
    authenticated_user["organization_info"] = (
        db.session.query(Organization)
        .filter(Organization.id == current_user.organization_id)
        .one()
        .to_dict()
    )
    if current_user.has_role("contractor"):
        authenticated_user["contractor_info"] = (
            db.session.query(ContractorInfo)
            .filter(ContractorInfo.id == current_user.id)
            .one()
            .to_dict()
        )
    else:
        authenticated_user["manager_info"] = (
            db.session.query(ManagerInfo)
            .filter(ManagerInfo.id == current_user.id)
            .one()
            .to_dict()
        )
    return {"authenticated_user": authenticated_user}, 200


@bp.route("/users/edit", methods=["PUT"])
@login_required
@roles_accepted("contractor")
def edit_user():
    phone = get_request_json(request, "phone")
    email = get_request_json(request, "email")

    db.session.query(User).filter(User.id == current_user.id).update(
        {User.phone: phone, User.email: email}
    )

    db.session.commit()
    result = current_user.to_dict()

    if current_user.has_role("contractor"):
        result["contractor_info"] = (
            db.session.query(ContractorInfo)
            .filter(ContractorInfo.id == current_user.id)
            .one()
            .to_dict()
        )
    else:
        result["manager_info"] = (
            db.session.query(ManagerInfo)
            .filter(ManagerInfo.id == current_user.id)
            .one()
            .to_dict()
        )

    emit_to_users(
        "ADD_USER", result, get_manager_user_ids(current_user.organization_id)
    )
    return {"event": result}, 200


@bp.route("/users/contractors/<user_id>", methods=["PATCH"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def edit_contractor(user_id):
    """Gives manager the ability to edit an contractor's pay and direct manager
    ---
    responses:
        200:
            description: Contractor edited
    """
    hourly_rate = get_request_json(request, "hourly_rate", optional=True)
    direct_manager = get_request_json(request, "direct_manager", optional=True)
    color = get_request_json(request, "color", optional=True)

    if direct_manager:
        db.session.query(User).filter(
            User.id == user_id, User.organization_id == current_user.organization_id
        ).update({User.manager_id: int(direct_manager)})
    if hourly_rate:
        db.session.query(ContractorInfo).filter(ContractorInfo.id == user_id).update(
            {ContractorInfo.hourly_rate: float(hourly_rate)}
        )
    if color:
        db.session.query(ContractorInfo).filter(ContractorInfo.id == user_id).update(
            {ContractorInfo.color: color}
        )
    db.session.commit()

    result = (
        db.session.query(User)
        .filter(
            User.id == user_id, User.organization_id == current_user.organization_id
        )
        .one()
        .to_dict()
    )
    result["contractor_info"] = (
        db.session.query(ContractorInfo)
        .filter(ContractorInfo.id == user_id)
        .one()
        .to_dict()
    )

    recipients = get_manager_user_ids(current_user.organization_id)
    recipients.append(user_id)

    emit_to_users("ADD_USER", result, recipients)

    return {"event": result}, 200


@bp.route("/users/organizations/me", methods=["GET"])
@login_required
@roles_accepted("organization_manager", "contractor_manager")
def list_contractors():
    """Returns list of contractors associated with the current user's organization
    ---
    responses:
        200:
            description: A list of users
            schema:
                $ref: '#/definitions/User'
    """
    result = (
        db.session.query(User)
        .filter(
            User.organization_id == current_user.organization_id, User.active == True
        )
        .all()
    )
    return {"users": [x.to_dict() for x in result]}, 200


@bp.route("/users/retry", methods=["PUT"])
@login_required
@roles_required("contractor")
def retry_contractor_payments():
    dwolla_request = request.get_json()
    first_name = get_request_json(request, "firstName")
    last_name = get_request_json(request, "lastName")
    dwolla_request["type"] = "personal"
    dwolla_request["email"] = current_user.email
    contractor_info = (
        db.session.query(ContractorInfo)
        .filter(ContractorInfo.id == current_user.id)
        .one()
    )
    status = payments.retry_personal_customer(
        dwolla_request, contractor_info.dwolla_customer_url
    )
    db.session.query(User).filter(User.id == current_user.id).update(
        {User.first_name: first_name, User.last_name: last_name}
    )
    db.session.query(ContractorInfo).filter(
        ContractorInfo.id == current_user.id
    ).update({ContractorInfo.dwolla_customer_status: status})
    db.session.commit()

    contractor_info = (
        db.session.query(ContractorInfo)
        .filter(ContractorInfo.id == current_user.id)
        .one()
        .to_dict()
    )
    result = current_user.to_dict()
    result["contractor_info"] = contractor_info

    return result


@bp.route("/users/me/location", methods=["POST"])
@login_required
def log_user_location():
    longitude = get_request_json(request, "longitude", optional=True)
    latitude = get_request_json(request, "latitude", optional=True)
    accuracy = get_request_json(request, "accuracy", optional=True)
    altitude_accuracy = get_request_json(request, "altitude_accuracy", optional=True)
    altitude = get_request_json(request, "altitude", optional=True)
    speed = get_request_json(request, "speed", optional=True)
    heading = get_request_json(request, "heading", optional=True)
    timestamp = get_request_json(request, "timestamp", optional=True)

    location = UserLocation(
        user_id=current_user.id,
        longitude=longitude,
        latitude=latitude,
        accuracy=accuracy,
        altitude_accuracy=altitude_accuracy,
        altitude=altitude,
        speed=speed,
        heading=heading,
        timestamp=datetime.datetime.fromtimestamp(timestamp / 1000.0, tz=pytz.utc),
    )
    db.session.add(location)
    db.session.commit()
    emit_to_users(
        "ADD_USER",
        {"id": current_user.id, "location": location.to_dict()},
        get_manager_user_ids(current_user.organization_id),
    )
    return OK_RESPONSE


@bp.route("/users/notifications", methods=["POST"])
@login_required
def add_push_registration():
    registration_id = get_request_json(request, "registration_id")

    registration = PushRegistration(
        user_id=current_user.id, registration_id=registration_id
    )
