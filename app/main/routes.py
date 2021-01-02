from app.main import bp as bp
import requests
from flask import render_template, current_app

# Direct all other traffic to Vue app
@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
def catch_all(path):
    if current_app._get_current_object().debug:
        return requests.get('http://localhost:8080/{}'.format(path)).text
    return render_template("index.html")