"""API package"""
from flask import Blueprint

from app.api import clock, users, job, scheduler, messenger, payment, calendar

bp = Blueprint('api', __name__)
