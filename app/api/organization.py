from flask_security import (
    current_user,
    login_required,
    roles_required,
    roles_accepted,
)
from flask import request
from app import db
from app.api import bp
from app.models import Organization
from app.utils import get_request_arg, get_request_json, OK_RESPONSE


@bp.route("/organization", methods=["GET"])
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
    return {"organization": result.to_dict()}


@bp.route("/organization", methods=["PATCH"])
@login_required
@roles_required("organization_manager")
def edit_organization():
    org_wage = float(get_request_json(request, "minimum_wage"))

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

    return {"organization": result}, 200
