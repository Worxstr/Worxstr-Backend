from werkzeug.exceptions import BadRequest


class MissingParameterException(BadRequest):
    pass


class NotEnoughInformationException(BadRequest):
    pass
