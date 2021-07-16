from flask import abort

from app.errors.customs import MissingParameterException


OK_RESPONSE = "OK"


def get_request_json(request, parameter, optional=False):
    if not request.json:
        abort(400)
    return get_key(request.json, parameter, not optional)


def get_request_arg(request, parameter, optional=False):
    if not request.args:
        abort(400)
    return get_key(request.args, parameter, not optional)


def get_key(obj, key, error_on_missing=False):
    value = obj.get(key)

    if error_on_missing and value is None:
        raise MissingParameterException(f'Request attribute not found: "{key}"')

    return value
