import requests

from flask import render_template, current_app

from app.main import bp as bp
from flask_security import current_user

# Direct all other traffic to Vue app
@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
def catch_all(path):
    url = 'http://' + current_app._get_current_object().config['BASE_URL']
    if current_app._get_current_object().debug:
        return requests.get(url.format(path)).text
    return "API Endpoint"