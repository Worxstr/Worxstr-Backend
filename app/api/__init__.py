"""API package"""
from flask import Blueprint

bp = Blueprint("api", __name__)

from app.api import (
    clock,
    users,
    job,
    scheduler,
    messenger,
    payment,
    calendar,
    contact,
    signup,
    organization,
    sockets,
    api,
    report,
)
