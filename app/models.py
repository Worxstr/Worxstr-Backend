from datetime import datetime
from enum import Enum

from flask_security import UserMixin, RoleMixin
from sqlalchemy_serializer import SerializerMixin

from app import db
from app.utils import get_key, get_request_arg, get_request_json


class CustomSerializerMixin(SerializerMixin):
    datetime_format = "%Y-%m-%dT%H:%M:%SZ"


class RolesUsers(db.Model):
    __tablename__ = "roles_users"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column("user_id", db.Integer(), db.ForeignKey("user.id"))
    role_id = db.Column("role_id", db.Integer(), db.ForeignKey("role.id"))


class Role(db.Model, RoleMixin, CustomSerializerMixin):

    serialize_only = ("id", "name")

    __tablename__ = "role"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return "<Role {}>".format(self.name)


class User(db.Model, UserMixin, CustomSerializerMixin):

    serialize_only = (
        "id",
        "email",
        "phone",
        "first_name",
        "last_name",
        "username",
        "organization_id",
        "manager_id",
    )
    serialize_rules = ()

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    phone = db.Column(db.String(10))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    username = db.Column(db.String(255))
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"))
    manager_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    password = db.Column(db.String(255))
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship(
        "Role", secondary="roles_users", backref=db.backref("users", lazy="dynamic")
    )


class ManagerReference(db.Model):
    __tablename__ = "manager_reference"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column("user_id", db.Integer(), db.ForeignKey("user.id"))
    reference_number = db.Column("reference_number", db.String(), unique=True)


class Organization(db.Model, CustomSerializerMixin):
    __tablename__ = "organization"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    primary_contact_first_name = db.Column(db.String(255))
    primary_contact_last_name = db.Column(db.String(255))
    primary_contact_phone = db.Column(db.String(10))
    primary_contact_email = db.Column(db.String(255))

    def __repr__(self):
        return "<Organization {}>".format(self.name)


class Job(db.Model, CustomSerializerMixin):
    __tablename__ = "job"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"))
    employee_manager_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    organization_manager_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    address = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    zip_code = db.Column(db.String(10))
    country = db.Column(db.String(255))
    consultant_name = db.Column(db.String(255))
    consultant_phone = db.Column(db.String(10))
    consultant_email = db.Column(db.String(255))
    consultant_code = db.Column(db.String(255))
    longitude = db.Column(db.Float(precision=52))
    latitude = db.Column(db.Float(precision=52))
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return "<Job {}>".format(self.name)


class ScheduleShift(db.Model, CustomSerializerMixin):
    __tablename__ = "schedule_shift"
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))
    time_begin = db.Column(db.DateTime)
    time_end = db.Column(db.DateTime)
    employee_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    site_location = db.Column(db.String(255))
    timecard_id = db.Column(db.Integer, db.ForeignKey("time_card.id"))

    def from_request(request):
        shift = get_request_json(request, "shift")
        job_id = get_request_arg(request, "job_id")

        time_begin = get_key(shift, "time_begin", error_on_missing=True)
        time_end = get_key(shift, "time_end", error_on_missing=True)
        site_location = get_key(shift, "site_location", error_on_missing=True)
        employee_id = get_key(shift, "employee_id", error_on_missing=True)

        return ScheduleShift(
            job_id=job_id,
            time_begin=time_begin,
            time_end=time_end,
            site_location=site_location,
            employee_id=employee_id,
        )


class TimeClockAction(Enum):
    clock_in = 1
    clock_out = 2
    start_break = 3
    end_break = 4


class TimeClock(db.Model, CustomSerializerMixin):
    __tablename__ = "time_clock"
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    action = db.Column(db.Enum(TimeClockAction))
    timecard_id = db.Column(db.Integer, db.ForeignKey("time_card.id"))
    employee_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class TimeCard(db.Model, CustomSerializerMixin):
    __tablename__ = "time_card"
    id = db.Column(db.Integer, primary_key=True)
    total_time = db.Column(db.Numeric)
    time_break = db.Column(db.Numeric)
    employee_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    wage_payment = db.Column(db.Numeric)
    fees_payment = db.Column(db.Numeric)
    total_payment = db.Column(db.Numeric)
    approved = db.Column(db.Boolean, default=False)
    paid = db.Column(db.Boolean, default=False)
    denied = db.Column(db.Boolean, default=False)
    transaction_id = db.Column(db.String(255))
    payout_id = db.Column(db.String(255))


class EmployeeInfo(db.Model, CustomSerializerMixin):
    serialize_only = (
        "id",
        "address",
        "city",
        "state",
        "zip_code",
        "longitude",
        "latitude",
        "hourly_rate",
        "need_info",
    )
    __tablename__ = "employee_info"
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    ssn = db.Column(db.String(9), unique=True)
    address = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    zip_code = db.Column(db.String(10))
    longitude = db.Column(db.Float(precision=52))
    latitude = db.Column(db.Float(precision=52))
    hourly_rate = db.Column(db.Numeric)
    need_info = db.Column(db.Boolean, default=False)


class Message(db.Model, CustomSerializerMixin):
    __tablename__ = "message"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversation.id"))

    def __repr__(self):
        return "<Message {}>".format(self.body)


class Conversation(db.Model, CustomSerializerMixin):
    __tablename__ = "conversation"
    id = db.Column(db.Integer, primary_key=True)
    participants = db.relationship("User", secondary="user_conversation")
    messages = db.relationship("Message")


user_conversation_table = db.Table(
    "user_conversation",
    db.Model.metadata,
    db.Column("conversation_id", db.Integer, db.ForeignKey("conversation.id")),
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
)
