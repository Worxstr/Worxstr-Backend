import requests

from flask import render_template, current_app, redirect

from app.main import bp as bp
from flask_security import current_user
from config import Config

# Direct all other traffic to Vue app
@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def catch_all(path):
    return redirect(Config.FRONT_URL, code=302)
