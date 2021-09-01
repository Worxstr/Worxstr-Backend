import datetime

from flask import request, render_template, current_app
from flask_security import (
    hash_password,
)

from app import db, user_datastore
from app.api import bp
from app.models import ManagerReference, User, ContractorInfo, Organization
from app.email import send_email
from app.utils import get_request_arg, get_request_json, OK_RESPONSE
from app import payments

from itsdangerous import URLSafeTimedSerializer


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

    customer_url = get_request_json(request, "customer_url")
    password = get_request_json(request, "password")
    customer = payments.get_customer_info(customer_url)

    organization_name = customer["businessName"]
    organization = Organization(
        name=organization_name, dwolla_customer_url=customer_url
    )
    db.session.add(organization)
    db.session.commit()

    roles = ["organization_manager", "contractor_manager"]
    user = user_datastore.create_user(
        first_name=customer["firstName"],
        last_name=customer["lastName"],
        email=customer["email"],
        organization_id=organization.id,
        dwolla_customer_url=customer_url,
        roles=roles,
        password=hash_password(password),
    )
    db.session.commit()
    send_confirmation_email(user.email, user.first_name)
    return user.to_dict()


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
    password = get_request_json(request, "password")
    manager_reference = get_request_json(request, "manager_reference")
    customer_url = get_request_json(request, "customer_url")

    customer = payments.get_customer_info(customer_url)

    first_name = customer["firstName"]
    last_name = customer["lastName"]
    email = customer["email"]

    roles = ["contractor"]
    manager_id = (
        db.session.query(ManagerReference.user_id)
        .filter(ManagerReference.reference_number == manager_reference)
        .one()[0]
    )
    organization_id = (
        db.session.query(User.organization_id).filter(User.id == manager_id).one()[0]
    )

    user = user_datastore.create_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        organization_id=organization_id,
        manager_id=manager_id,
        dwolla_customer_url=customer_url,
        roles=roles,
        password=hash_password(password),
    )
    db.session.commit()

    contractor_info = ContractorInfo(id=user.id)
    db.session.add(contractor_info)
    db.session.commit()
    send_confirmation_email(user.email, user.first_name)
    return user.to_dict(), 201


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
    return {"message": "Invalid token"}, 401


@bp.route("/auth/resend-email", methods=["POST"])
def test():
    email = get_request_json(request, "email")
    name = get_request_json(request, "name", True) or "User"
    send_confirmation_email(email, name)
    return OK_RESPONSE


def send_confirmation_email(email, name):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    token = serializer.dumps(email, salt=current_app.config["SECURITY_PASSWORD_SALT"])
    send_email(
        "[Worxstr] Please Confirm your email",
        sender=current_app.config["ADMINS"][0],
        recipients=[email],
        text_body=render_template(
            "email/confirm_email.txt",
            token=token,
            user=name,
            email=email,
            url=current_app.config["FRONT_URL"],
        ),
        html_body=render_template(
            "email/confirm_email.html",
            token=token,
            user=name,
            email=email,
            url=current_app.config["FRONT_URL"],
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
