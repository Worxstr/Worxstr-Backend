from flask_security import (
    login_required,
)
from app.api import bp
from config import Config


@bp.route("/info", methods=["GET"])
@login_required
def info():
    return {"app_version": Config.APP_VERSION}
