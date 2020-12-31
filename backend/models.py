from flask_security import UserMixin, RoleMixin
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey

class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    phone = Column(String(10))
    first_name = Column(String(255))
    last_name = Column(String(255))
    username = Column(String(255))
    password = Column(String(255))
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    current_login_ip = Column(String(100))
    login_count = Column(Integer)
    active = Column(Boolean())
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('users', lazy='dynamic'))

class Organization(db.Model):
    __tablename__ = 'organization'
    id = Column(Integer, primary_key=True)
    primary_manager = Column(Integer, ForeignKey('user.id'))

class Job(db.Model):
    __tablename__ = 'job'
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organization.id'))
    employee_manager_id = Column(Integer, ForeignKey('user.id'))
    orgizational_manager_id = Column(Integer, ForeignKey('user.id'))
    address = Column(String(255))
    city = Column(String(255))
    state = Column(String(255))
    zip_code = Column(String(10))
    consultant_name = Column(String(255))
    consultant_phone = Column(String(10))

class Shift(db.Model):
    __tablename__ = 'shift'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('job.id'))
    time_begin = Column(DateTime)
    time_end = Column(DateTime)
    employee_id = Column(Integer, ForeignKey('user.id'))
    site_location = Column(String(255))

class EmployeeInfo(db.Model):
    __tablename__ = 'employee_info'
    id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    ssn = Column(String(9))
    address = Column(String(255))
    city = Column(String(255))
    state = Column(String(255))
    zip_code = Column(String(10))