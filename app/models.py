from enum import Enum

from flask_security import UserMixin, RoleMixin

from app import db

class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column('user_id', db.Integer(), db.ForeignKey('user.id'))
    role_id = db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return '<Role {}>'.format(self.name)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    phone = db.Column(db.String(10))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary='roles_users', backref=db.backref('users', lazy='dynamic'))
    
    def __repr__(self):
        return '<User {}>'.format(self.username)

class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    primary_manager = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Organization {}>'.format(self.name)

class Job(db.Model):
    __tablename__ = 'job'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    employee_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    orgizational_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    address = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    zip_code = db.Column(db.String(10))
    consultant_name = db.Column(db.String(255))
    consultant_phone = db.Column(db.String(10))
    consultant_code = db.Column(db.String(255))

    def __repr__(self):
        return '<Job {}>'.format(self.name)

class ScheduleShift(db.Model):
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

class TimeClock(db.Model):
    __tablename__ = 'time_clock'
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    action = db.Column(db.Enum(TimeClockAction))
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class EmployeeInfo(db.Model):
    __tablename__ = 'employee_info'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    ssn = db.Column(db.String(9), unique=True)
    address = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    zip_code = db.Column(db.String(10))
