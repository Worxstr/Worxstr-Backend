import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):

    BASE_URL = os.environ.get("BASE_URL") or "localhost:5000/{}"
    FRONT_URL = os.environ.get("FRONT_URL") or "localhost:8080/"

    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"

    # Database config
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "max_overflow": 15,
        "pool_pre_ping": True,
        "pool_recycle": 60 * 60,
        "pool_size": 30,
    }

    # Mail Server config
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    ADMINS = ["support@worxstr.com", "admin@worxstr.com"]

    # Application threads. A common general assumption is
    # using 2 per available processor cores - to handle
    # incoming requests using one and performing background
    # operations using the other.
    THREADS_PER_PAGE = 2

    # no forms so no concept of flashing
    SECURITY_FLASH_MESSAGES = False

    # Need to be able to route backend flask API calls. Use 'auth'
    # to be the Flask-Security endpoints.
    SECURITY_URL_PREFIX = "/auth"

    # Turn on all the great Flask-Security features
    SECURITY_RECOVERABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_CONFIRMABLE = True
    SECURITY_REGISTERABLE = True
    SECURITY_UNIFIED_SIGNIN = False

    # These need to be defined to handle redirects
    # As defined in the API documentation - they will receive the relevant context
    SECURITY_RESET_VIEW = FRONT_URL + "/auth/reset"
    SECURITY_RESET_ERROR_VIEW = FRONT_URL + "/auth/reset/error"
    SECURITY_REDIRECT_BEHAVIOR = "spa"
    SECURITY_PASSWORD_SALT = (
        os.environ.get("SECURITY_PASSWORD_SALT")
        or "146585145368132386173505678016728509634"
    )

    # CSRF protection is critical for all session-based browser UIs
    # enforce CSRF protection for session / browser - but allow token-based
    # API calls to go through
    SECURITY_CSRF_PROTECT_MECHANISMS = ["session", "basic"]
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True

    # Send Cookie with csrf-token. This is the default for Axios and Angular.
    SECURITY_CSRF_COOKIE = {
        "key": os.environ.get("SECURITY_PASSWORD_SALT")
        or "146585145368132386173505678016728509634ebeb"
    }
    WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_TIME_LIMIT = None

    SWAGGER_CONFIG = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "static_url_path": "/flasgger_static",
        # "static_folder": "static",  # must be set by user
        "swagger_ui": True,
        "specs_route": "/docs/",
    }

    CLICKUP_KEY = os.environ.get("CLICKUP_KEY")
    DWOLLA_APP_KEY = os.environ.get("DWOLLA_APP_KEY")
    DWOLLA_APP_SECRET = os.environ.get("DWOLLA_APP_SECRET")
    DWOLLA_HOST = os.environ.get("DWOLLA_HOST")
    DWOLLA_WEBHOOK_SECRET = (
        os.environ.get("DWOLLA_WEBHOOK_SECRET")
        or "146585145368132386173505678016728509634"
    )
    PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID")
    PLAID_SECRET = os.environ.get("PLAID_SECRET")
    PLAID_HOST = os.environ.get("PLAID_HOST")

    FIREBASE_SERVER_KEY = os.environ.get("FIREBASE_SERVER_KEY")
