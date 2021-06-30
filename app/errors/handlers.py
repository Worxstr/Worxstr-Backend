from flask import json

from app import db
from app.errors import bp
from app.errors.customs import MissingParameterException, NotEnoughInformationException


@bp.app_errorhandler(MissingParameterException)
def missing_parameter_error(error):
    response = error.get_response()

    response.content_type = "application/json"
    response.data = json.dumps(
        {
            "message": error.description,
        }
    )

    return response


@bp.app_errorhandler(NotEnoughInformationException)
def not_enough_information(error):
    response = error.get_response()

    response.content_type = "application/json"
    response.data = json.dumps(
        {
            "message": error.description,
        }
    )

    return response


@bp.app_errorhandler(404)
def not_found_error(error):
    return 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return 500
