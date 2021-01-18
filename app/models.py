import pytz

from datetime import datetime
from enum import Enum

from flask_security import UserMixin, RoleMixin
from sqlalchemy_serializer import SerializerMixin

from app import db

class CustomSerializerMixin(SerializerMixin):
    datetime_format = '%Y-%m-%d %H:%M:%S UTC'

class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column('user_id', db.Integer(), db.ForeignKey('user.id'))
    role_id = db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))

class Role(db.Model, RoleMixin, CustomSerializerMixin):

    serialize_only = ('id', 'name')

    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return '<Role {}>'.format(self.name)

class User(db.Model, UserMixin, CustomSerializerMixin):

    serialize_only = ('id', 'email', 'phone', 'first_name', 'last_name', 'username', 'organization_id')
    serialize_rules = ()

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    phone = db.Column(db.String(10))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    username = db.Column(db.String(255))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    password = db.Column(db.String(255))
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary='roles_users', backref=db.backref('users', lazy='dynamic'))
    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()

class Organization(db.Model, CustomSerializerMixin):
    __tablename__ = 'organization'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    primary_contact_first_name = db.Column(db.String(255))
    primary_contact_last_name = db.Column(db.String(255))
    primary_contact_phone = db.Column(db.String(10))
    primary_contact_email = db.Column(db.String(255))

    def __repr__(self):
        return '<Organization {}>'.format(self.name)

class Job(db.Model, CustomSerializerMixin):
    __tablename__ = 'job'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    employee_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    organizational_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    address = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    zip_code = db.Column(db.String(10))
    consultant_name = db.Column(db.String(255))
    consultant_phone = db.Column(db.String(10))
    consultant_email = db.Column(db.String(255))
    consultant_code = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return '<Job {}>'.format(self.name)

class ScheduleShift(db.Model, CustomSerializerMixin):
    __tablename__ = 'schedule_shift'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    time_begin = db.Column(db.DateTime)
    time_end = db.Column(db.DateTime)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    site_location = db.Column(db.String(255))

class TimeClockAction(Enum):
    clock_in = 1
    clock_out = 2
    start_break = 3
    end_break = 4

class TimeClock(db.Model, CustomSerializerMixin):
    __tablename__ = 'time_clock'
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    action = db.Column(db.Enum(TimeClockAction))
    timecard_id = db.Column(db.Integer, db.ForeignKey('time_card.id'))
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class TimeCard(db.Model, CustomSerializerMixin):
    __tablename__ = 'time_card'
    id = db.Column(db.Integer, primary_key=True)
    total_time = db.Column(db.Numeric)
    time_break = db.Column(db.Numeric)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    wage_payment = db.Column(db.Numeric)
    fees_payment = db.Column(db.Numeric)
    total_payment = db.Column(db.Numeric)
    approved = db.Column(db.Boolean, default=False)
    paid = db.Column(db.Boolean, default=False)
    denied = db.Column(db.Boolean, default=False)
    transaction_id = db.Column(db.String(255))
    payout_id = db.Column(db.String(255))

class EmployeeInfo(db.Model):
    __tablename__ = 'employee_info'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    ssn = db.Column(db.String(9), unique=True)
    address = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    zip_code = db.Column(db.String(10))
    hourly_rate = db.Column(db.Numeric)

class Message(db.Model, CustomSerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)