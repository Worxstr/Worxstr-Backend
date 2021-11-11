from datetime import datetime
from enum import Enum

from flask_security import UserMixin, RoleMixin, current_user
from sqlalchemy.sql.expression import null
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.hybrid import hybrid_property
from app import db
from app.utils import get_key, get_request_arg, get_request_json


class CustomSerializerMixin(SerializerMixin):
    datetime_format = "%Y-%m-%dT%H:%M:%SZ"


class RolesUsers(db.Model):
    __tablename__ = "roles_users"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column("user_id", db.Integer(), db.ForeignKey("user.id"))
    role_id = db.Column("role_id", db.Integer(), db.ForeignKey("role.id"))


class Sessions(db.Model):
    __tablename__ = "sessions"
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))
    session_id = db.Column(db.String(50), primary_key=True)


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
        "organization_id",
        "manager_id",
        "dwolla_customer_url",
        "roles",
        "direct",
        "fs_uniquifier",
    )
    serialize_rules = ()

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    phone = db.Column(db.String(10))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
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
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)

    @hybrid_property
    def dwolla_customer_url(self):
        customer_url = None
        if self.has_role("contractor"):
            customer_url = (
                db.session.query(ContractorInfo.dwolla_customer_url)
                .filter(ContractorInfo.id == self.id)
                .one()[0]
            )
        else:
            customer_url = (
                db.session.query(Organization.dwolla_customer_url)
                .filter(Organization.id == self.organization_id)
                .one()[0]
            )
        return customer_url

    @hybrid_property
    def direct(self):
        if current_user.is_authenticated:
            return int(current_user.id) == self.manager_id
        else:
            return None


class ManagerInfo(db.Model, CustomSerializerMixin):
    serialize_only = ("reference_number",)
    __tablename__ = "manager_info"
    id = db.Column("user_id", db.Integer(), db.ForeignKey("user.id"), primary_key=True)
    reference_number = db.Column("reference_number", db.String(), unique=True)


class Organization(db.Model, CustomSerializerMixin):
    __tablename__ = "organization"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    dwolla_customer_url = db.Column(db.String(255))
    dwolla_customer_status = db.Column(db.String(10))
    minimum_wage = db.Column(db.Numeric, nullable=False, default=7.5)

    def __repr__(self):
        return "<Organization {}>".format(self.name)


class Job(db.Model, CustomSerializerMixin):
    serialize_rules = ("direct",)

    __tablename__ = "job"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"))
    contractor_manager_id = db.Column(db.Integer, db.ForeignKey("user.id"))
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
    color = db.Column(db.String(7))
    radius = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return "<Job {}>".format(self.name)

    @hybrid_property
    def direct(self):
        return (
            int(current_user.id) == self.contractor_manager_id
            or int(current_user.id) == self.organization_manager_id
        )


class ScheduleShift(db.Model, CustomSerializerMixin):
    __tablename__ = "schedule_shift"
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))
    time_begin = db.Column(db.DateTime)
    time_end = db.Column(db.DateTime)
    contractor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    site_location = db.Column(db.String(255))
    timecard_id = db.Column(db.Integer, db.ForeignKey("time_card.id"))

    def from_request(request):
        shift = get_request_json(request, "shift")
        job_id = get_request_arg(request, "job_id")

        time_begin = get_key(shift, "time_begin", error_on_missing=True)
        time_end = get_key(shift, "time_end", error_on_missing=True)
        site_location = get_key(shift, "site_location", error_on_missing=True)
        contractor_id = get_key(shift, "contractor_id", error_on_missing=True)

        return ScheduleShift(
            job_id=job_id,
            time_begin=time_begin,
            time_end=time_end,
            site_location=site_location,
            contractor_id=contractor_id,
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
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))
    shift_id = db.Column(db.Integer, db.ForeignKey("schedule_shift.id"))
    contractor_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class TimeCard(db.Model, CustomSerializerMixin):
    serialize_rules = (
        "first_name",
        "last_name",
    )

    __tablename__ = "time_card"
    id = db.Column(db.Integer, primary_key=True)
    total_time = db.Column(db.Numeric)
    time_break = db.Column(db.Numeric)
    contractor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    wage_payment = db.Column(db.Numeric)
    fees_payment = db.Column(db.Numeric)
    total_payment = db.Column(db.Numeric)
    paid = db.Column(db.Boolean, default=False)
    denied = db.Column(db.Boolean, default=False)

    @hybrid_property
    def first_name(self):
        return (
            db.session.query(User.first_name)
            .filter(User.id == self.contractor_id)
            .one()[0]
        )

    @hybrid_property
    def last_name(self):
        return (
            db.session.query(User.last_name)
            .filter(User.id == self.contractor_id)
            .one()[0]
        )


class ContractorInfo(db.Model, CustomSerializerMixin):
    serialize_only = ("hourly_rate",)
    __tablename__ = "contractor_info"
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    hourly_rate = db.Column(db.Numeric)
    dwolla_customer_url = db.Column(db.String(255))
    dwolla_customer_status = db.Column(db.String(10))


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
