from flask import Flask, render_template
from flasgger import Swagger
from random import *
from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, hash_password
from sqlalchemy import Boolean, DateTime, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
# from flask_migrate import Migrate
# from flask_session import Session
import flask_wtf
import requests

from backend.api import api



########################################################
app = Flask(
    __name__,
    static_folder = "./frontend/dist",
    template_folder = "./frontend/dist"
)
########################################################


app.config.from_object('config')


# Initialize Flask-Security
db = SQLAlchemy(app)


# Define models
roles_users = db.Table('roles_users',
        Column('user_id', Integer(), ForeignKey('user.id')),
        Column('role_id', Integer(), ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(db.String(255))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
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

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)



# In your app
# Enable CSRF on all api endpoints.
flask_wtf.CSRFProtect(app)

# mail = Mail(app)


########################################################
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
########################################################


@app.before_first_request
def create_user():
    db.create_all()
    # password = hash_password('plaintext')
    # user_datastore.create_user(email='alexwohlbruck@gmail.com', password=password)
    db.session.commit()



# @app.route('/auth/sign-up')
# def sign_up():
#     return 'asdf'

# @app.route('/auth/sign-in')
# def sign_in():
    

########################################################
# Direct all other traffic to Vue app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if app.debug:
        return requests.get('http://localhost:8080/{}'.format(path)).text
    return render_template("index.html")

if __name__ == '__main__':
    app.run()
########################################################