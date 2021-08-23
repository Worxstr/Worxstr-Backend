import datetime

from flask import request
from flask_security import (
    hash_password,
)

from app import db, user_datastore
from app.api import bp
from app.models import ManagerReference, User, ContractorInfo, Organization
from app.utils import get_request_arg, get_request_json, OK_RESPONSE
from app import payments


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

    confirmed_at = datetime.datetime.utcnow()
    roles = ["organization_manager", "contractor_manager"]
    user = user_datastore.create_user(
        first_name=customer["firstName"],
        last_name=customer["lastName"],
        email=customer["email"],
        organization_id=organization.id,
        dwolla_customer_url=customer_url,
        confirmed_at=confirmed_at,
        roles=roles,
        password=hash_password(password),
    )
    db.session.commit()
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