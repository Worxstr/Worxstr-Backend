from flask_security import (
    current_user,
    login_required,
    roles_required,
    roles_accepted,
)
from flask import request
from sqlalchemy.sql.elements import Null
from app import db
from app.api import bp
from app.models import Organization, User, Role
from app.utils import get_request_arg, get_request_json, OK_RESPONSE
from app.api.sockets import emit_to_users
from app import payments


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


@bp.route("/organizations/me", methods=["GET"])
@login_required
def get_organization():
    """
    Returns detail of current user's organization
    ---
    responses:
        200:
            description: An organization
            schema:
                type: array
                items:
                    $ref: '#/definitions/Organization'
    """
    result = (
        db.session.query(Organization)
        .filter(Organization.id == current_user.organization_id)
        .one()
    )
    return result.to_dict()


@bp.route("/organizations/me", methods=["PATCH"])
@login_required
@roles_required("organization_manager")
def edit_organization():
    org_wage = float(get_request_json(request, "default_wage"))

    db.session.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).update({Organization.minimum_wage: org_wage})

    db.session.commit()
    org = (
        db.session.query(Organization)
        .filter(Organization.id == current_user.organization_id)
        .one()
    )
    result = org.to_dict()

    user_ids = get_manager_user_ids(current_user.organization_id)

    emit_to_users("ADD_ORGANIZATION", result, user_ids)

    return result, 200


@bp.route("/organizations/retry", methods=["PUT"])
@login_required
@roles_required("organization_manager")
def retry_organization_payments():
    dwolla_request = request.get_json()
    dwolla_request["type"] = "business"
    dwolla_request["email"] = db.session.query(User.email).filter(User.organization_id == current_user.organization_id, User.manager_id == None).one()[0]
    status = payments.retry_business_customer(dwolla_request)
    db.session.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).update({Organization.dwolla_customer_status: status})
    db.session.commit()
    response = current_user.to_dict()
    response["organization_info"] = (
        db.session.query(Organization)
        .filter(Organization.id == current_user.organization_id)
        .one()
        .to_dict()
    )
    return response
