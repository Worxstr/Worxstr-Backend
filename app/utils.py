from flask import abort

from app.errors.customs import MissingParameterException


OK_RESPONSE = "OK"

# Get data from a response body
def get_request_json(request, parameter, optional=False):
    if not request.json:
        abort(400)
    return get_key(request.json, parameter, not optional)


def get_request_arg(request, parameter, optional=False):
    if not request.args:
        abort(400)
    return get_key(request.args, parameter, not optional)


# Get data from a dictionary. Recursive on nested dictionaries, separated by '.'
def get_key(obj, key, error_on_missing=False):

    if "." in key:
        key, rest = key.split(".", 1)
        if key not in obj:
            if error_on_missing:
                raise MissingParameterException(key)
            return None
        return get_key(obj.get(key), rest, error_on_missing)

    if key not in obj:
        if error_on_missing:
            raise MissingParameterException(f'Request attribute not found: "{key}"')
        return None

    return obj.get(key)
