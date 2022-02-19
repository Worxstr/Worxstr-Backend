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


# Flatten a dictionary
# TODO: Can't flatten lists yet
# Example:
# {
#     "a": {
#         "b": {
#             "c": 1,
#             "d": 2
#         },
#         "e": 3
#     },
#     "f": 4
# }
#
# becomes:
# {
#     "a.b.c": 1,
#     "a.b.d": 2,
#     "a.e": 3,
#     "f": 4
# }
def flatten_dict(dd: dict, separator=".", prefix="") -> dict:
    return (
        {
            prefix + separator + k if prefix else k: v
            for kk, vv in dd.items()
            for k, v in flatten_dict(vv, separator, kk).items()
        }
        if isinstance(dd, dict)
        else {prefix: dd}
    )


# Flatten a list of dictionaries
def flatten_dict_list(l: list) -> list:
    return [flatten_dict(d) for d in l]


# Convert a list of dictionaries to a CSV string.
def list_to_csv(dict_list: list, separator=",") -> str:

    # Flatten dictionaries before proceeding
    # TODO: This function doesn't flatten lists, so the commas in a list will mess up the output
    dict_list = flatten_dict_list(dict_list)

    print(flatten_dict(dict_list[0]))

    # Get unique keys
    keys = set()
    for d in dict_list:
        keys.update(d.keys())
    keys = sorted(list(keys))

    # Create headers
    csv = separator.join(keys) + "\n"

    # Create rows
    for d in dict_list:
        row = []
        for k in keys:
            row.append(str(d.get(k, "")))
        csv += separator.join(row) + "\n"

    return csv
