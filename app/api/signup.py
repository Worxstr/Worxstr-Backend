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

from app import db, user_datastore, geolocator
from app.api import bp
from app.email import send_email
from app.models import ManagerReference, User, ContractorInfo, Organization
from app.utils import get_request_arg, get_request_json, OK_RESPONSE


@bp.route("/signup/add-org", methods=["POST"])
def add_org():
    """Add an organization and new initial user

    The created user is considered the owner of the organization.
    ---

    responses:
        200:
            description: A new User who is the root user of the new Organization
            schema:
                    $ref: '#/definitions/User'
    """
    organization_name = get_request_json(request, "organization_name")

    organization = Organization(name=organization_name)
    db.session.add(organization)
    db.session.commit()
    user = {
        "first_name": get_request_json(request, "first_name"),
        "last_name": get_request_json(request, "last_name"),
        "username": get_request_json(request, "username"),
        "email": get_request_json(request, "email"),
        "phone": get_request_json(request, "phone"),
        "password": hash_password(get_request_json(request, "password")),
        "roles": ["organization_manager", "contractor_manager"],
        "manager_id": None,
        "organization_id": organization.id,
    }

    user = user_datastore.create_user(**user)
    db.session.commit()
    return user.to_dict()


@bp.route("/users/add-contractor", methods=["POST"])
def add_contractor():
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
    manager_reference = get_request_json(request, "manager_reference", optional=True)
    customer_url = get_request_json(request, "customer_url")

    confirmed_at = datetime.datetime.utcnow()
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
        confirmed_at=confirmed_at,
        roles=roles,
        password=hash_password(password),
    )
    db.session.commit()

    contractor_info = ContractorInfo(id=user.id)
    db.session.add(contractor_info)
    db.session.commit()

    return user.to_dict(), 201
