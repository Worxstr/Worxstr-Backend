from flask import Blueprint

bp = Blueprint('app', __name__)

from app.main import routes