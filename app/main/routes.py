import requests

from flask import render_template, current_app

from app.main import bp as bp
from flask_security import current_user

# Direct all other traffic to Vue app
@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def catch_all(path):
    return "API Endpoint"
