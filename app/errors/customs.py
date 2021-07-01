from werkzeug.exceptions import BadRequest


class MissingParameterException(BadRequest):
    pass
