from flask_security import (
    current_user,
    login_required,
    roles_required,
    roles_accepted,
)

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
    return {"organization":result.to_dict()}
