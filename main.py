from flask import Flask, render_template
from flasgger import Swagger
from random import *
from flask_cors import CORS
import requests

from backend.api import api

app = Flask(
    __name__,
    static_folder = "./frontend/dist",
    template_folder = "./frontend/dist"
)
            
app.register_blueprint(api)

swagger_config = {
    "headers": [
    ],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    # "static_folder": "static",  # must be set by user
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, config=swagger_config)

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


# Direct all other traffic to Vue app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if app.debug:
        return requests.get('http://localhost:8080/{}'.format(path)).text
    return render_template("index.html")
