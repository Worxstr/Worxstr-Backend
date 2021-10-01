import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_security import Security, SQLAlchemyUserDatastore
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from flask_socketio import SocketIO
from flasgger import Swagger
from geopy.geocoders import Nominatim

from config import Config
from app.payments.dwolla import Dwolla
from app.payments.plaid import Plaid

from apscheduler.schedulers.background import BackgroundScheduler

cors = CORS()
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
swagger = Swagger(config=Config.SWAGGER_CONFIG)
from app.models import User, Role

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()
csrf = CSRFProtect()
socketio = SocketIO()
geolocator = Nominatim(user_agent="worxstr")
payments = Dwolla(app_key=Config.DWOLLA_APP_KEY, app_secret=Config.DWOLLA_APP_SECRET, host=Config.DWOLLA_HOST)
payments_auth = Plaid(
    client_id=Config.PLAID_CLIENT_ID, secret=Config.PLAID_SECRET, host=Config.PLAID_HOST
)
scheduler = BackgroundScheduler()


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="./frontend/dist")

    app.config.from_object(config_class)
    cors.init_app(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    swagger.init_app(app)
    security.init_app(app, user_datastore)
    socketio.init_app(app, cors_allowed_origins="*")
    scheduler.add_job(func=payments.refresh_app_token, trigger="interval", seconds=3600)
    scheduler.start()

    @security.login_manager.unauthorized_handler
    def unauthorized_handler():
        return (
            jsonify(
                success=False,
                data={"login_required": True},
                message="Authorize please to access this page.",
            ),
            401,
        )

    csrf.init_app(app)

    from app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    from app.api import bp as api_bp

    app.register_blueprint(api_bp)

    if not app.debug:
        if app.config["MAIL_SERVER"]:
            auth = None
            if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
                auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            secure = None
            if app.config["MAIL_USE_TLS"]:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
                fromaddr="no-reply@" + app.config["MAIL_SERVER"],
                toaddrs=app.config["ADMINS"],
                subject="Worxstr Failure",
                credentials=auth,
                secure=secure,
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists("logs"):
            os.mkdir("logs")

        app.logger.setLevel(logging.INFO)
        app.logger.info("Worxstr startup")

    return app


from app import models
