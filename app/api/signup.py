import datetime

from flask import request, render_template, current_app
from flask_security import (
    hash_password,
)

from app import db, user_datastore, payments
from app.api import bp
from app.api.users import manager_reference_generator
from app.models import (
    ManagerInfo,
    SubscriptionTier,
    User,
    ContractorInfo,
    Organization,
    Role,
)
from app.email import send_email
from app.utils import get_request_arg, get_request_json, OK_RESPONSE
from app import payments
from app.api.sockets import emit_to_users

from dwollav2.error import ValidationError
from itsdangerous import URLSafeTimedSerializer
from urllib.parse import quote, urlencode


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


@bp.route("/auth/sign-up/org", methods=["POST"])
def sign_up_org():
    """Add an organization and new initial user

    The created user is considered the owner of the organization.
    ---
    parameters:
        - name: customer_url
          in: body
          type: string
        - name: password
          in: body
          type: string
    responses:
        200:
            description: A new User who is the root user of the new Organization
            schema:
                    $ref: '#/definitions/User'
    """

    first_name = get_request_json(request, "firstName")
    last_name = get_request_json(request, "lastName")
    email = get_request_json(request, "email")
    phone_raw = get_request_json(request, "phone")
    phone = phone_raw["areaCode"] + phone_raw["phoneNumber"]
    business_name = get_request_json(request, "businessName")
    password = get_request_json(request, "password")
    subscription_tier_code = get_request_json(request, "subscription_tier")

    dwolla_request = request.get_json()
    dwolla_request["type"] = "business"

    subscription_tier = (
        db.session.query(SubscriptionTier)
        .filter(SubscriptionTier.tier_code == subscription_tier_code)
        .one()
    )

    dwolla_customer_url = payments.create_business_customer(dwolla_request)
    if type(dwolla_customer_url) == tuple:
        return dwolla_customer_url
    if type(dwolla_customer_url) == tuple and "error" in dwolla_customer_url[0]:
        return dwolla_customer_url

    dwolla_customer_status = payments.get_customer_info(dwolla_customer_url)["status"]

    organization_name = business_name
    organization = Organization(
        name=organization_name,
        dwolla_customer_url=dwolla_customer_url,
        dwolla_customer_status=dwolla_customer_status,
        subscription_tier_id=subscription_tier.id,
        creation_date=datetime.datetime.utcnow(),
    )
    db.session.add(organization)
    db.session.commit()

    roles = ["organization_manager", "contractor_manager"]
    user = user_datastore.create_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        organization_id=organization.id,
        roles=roles,
        password=hash_password(password),
    )

    db.session.commit()
    manager_reference = ManagerInfo(
        id=user.id, reference_number=manager_reference_generator()
    )
    db.session.add(manager_reference)
    db.session.commit()
    send_confirmation_email(user.email, user.first_name)
    return OK_RESPONSE


@bp.route("/auth/sign-up/contractor", methods=["POST"])
def sign_up_contractor():
    """
    Add a new contractor.
    ---
    parameters:
        - name: customer_url
          in: body
          type: string
        - name: password
          in: body
          type: string
        - name: manager_reference
          in: body
          type: string
    responses:
        201:
            description: Contractor successfully created.
    """
    first_name = get_request_json(request, "firstName")
    last_name = get_request_json(request, "lastName")
    email = get_request_json(request, "email")
    phone_raw = get_request_json(request, "phone")
    phone = phone_raw["areaCode"] + phone_raw["phoneNumber"]
    password = get_request_json(request, "password")
    manager_reference = get_request_json(request, "manager_reference")
    color = get_request_json(request, "color")
    dwolla_request = request.get_json()
    manager_info = (
        db.session.query(ManagerInfo)
        .filter(ManagerInfo.reference_number == manager_reference)
        .one_or_none()
    )
    if manager_info == None:
        return {"message": "Invalid manager reference number."}, 401
    dwolla_request["type"] = "personal"
    dwolla_customer_url = payments.create_personal_customer(dwolla_request)
    if type(dwolla_customer_url) == tuple:
        return dwolla_customer_url
    dwolla_customer_status = payments.get_customer_info(dwolla_customer_url)["status"]
    roles = ["contractor"]
    manager_id = manager_info.id
    organization_id = (
        db.session.query(User.organization_id).filter(User.id == manager_id).one()[0]
    )

    wage = (
        db.session.query(Organization.minimum_wage)
        .filter(Organization.id == organization_id)
        .one()[0]
    )

    user = user_datastore.create_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        organization_id=organization_id,
        manager_id=manager_id,
        roles=roles,
        password=hash_password(password),
    )
    db.session.commit()

    contractor_info = ContractorInfo(
        id=user.id,
        dwolla_customer_url=dwolla_customer_url,
        hourly_rate=wage,
        dwolla_customer_status=dwolla_customer_status,
        color=color,
    )
    db.session.add(contractor_info)
    db.session.commit()
    send_confirmation_email(user.email, user.first_name)
    user_ids = get_manager_user_ids(organization_id)

    emit_to_users("ADD_USER", user.to_dict(), user_ids)
    emit_to_users("ADD_WORKFORCE_MEMBER", user.id, user_ids)

    return OK_RESPONSE


@bp.route("/auth/confirm-email", methods=["PUT"])
def confirm_email():
    token = get_request_json(request, "token")
    email = confirm_token(token)
    if email:
        db.session.query(User).filter(User.email == email).update(
            {User.confirmed_at: datetime.datetime.utcnow()}
        )
        db.session.commit()
        return OK_RESPONSE
    return {"message": "Invalid token."}, 401


@bp.route("/auth/resend-email", methods=["POST"])
def test():
    email = get_request_json(request, "email")
    name = get_request_json(request, "name", True) or "User"
    send_confirmation_email(email, name)
    return OK_RESPONSE


def send_confirmation_email(email, name):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    token = serializer.dumps(email, salt=current_app.config["SECURITY_PASSWORD_SALT"])
    params = {"token": token, "email": email}
    confirmation_url = (
        current_app.config["FRONT_URL"] + "/confirm-email" + "?" + urlencode(params)
    )
    print(confirmation_url)
    send_email(
        "[Worxstr] Please Confirm your email",
        sender=current_app.config["ADMINS"][0],
        recipients=[email],
        text_body=render_template(
            "email/confirm_email.txt",
            token=quote(token),
            user=name,
            email=quote(email),
            url=confirmation_url,
        ),
        html_body=render_template(
            "email/confirm_email.html",
            token=quote(token),
            user=name,
            email=quote(email),
            url=confirmation_url,
        ),
    )
    return OK_RESPONSE


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token, salt=current_app.config["SECURITY_PASSWORD_SALT"], max_age=expiration
        )
    except:
        return False
    return email
