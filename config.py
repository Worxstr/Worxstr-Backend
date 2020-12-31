# Statement for enabling the development environment
DEBUG = True

# Define the application directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  

# Define the database - we are working with
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432/worxstr"
DATABASE_CONNECT_OPTIONS = {}

SECRET_KEY = 'secret'



# from flask_mail import Mail

MAIL_SERVER = 'smtp.example.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = 'username'
MAIL_PASSWORD = 'password'




# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# no forms so no concept of flashing
SECURITY_FLASH_MESSAGES = False

# Need to be able to route backend flask API calls. Use 'auth'
# to be the Flask-Security endpoints.
SECURITY_URL_PREFIX = '/api/auth'

# Turn on all the great Flask-Security features
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True
SECURITY_CHANGEABLE = True
SECURITY_CONFIRMABLE = True
SECURITY_REGISTERABLE = True
SECURITY_UNIFIED_SIGNIN = False

# These need to be defined to handle redirects
# As defined in the API documentation - they will receive the relevant context
SECURITY_POST_CONFIRM_VIEW = "/confirmed"
SECURITY_CONFIRM_ERROR_VIEW = "/confirm-error"
SECURITY_RESET_VIEW = "/reset-password"
SECURITY_RESET_ERROR_VIEW = "/reset-password"
SECURITY_REDIRECT_BEHAVIOR = "spa"
SECURITY_PASSWORD_SALT = "test1234"
# CSRF protection is critical for all session-based browser UIs

# enforce CSRF protection for session / browser - but allow token-based
# API calls to go through
SECURITY_CSRF_PROTECT_MECHANISMS = ["session", "basic"]
SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True

# Send Cookie with csrf-token. This is the default for Axios and Angular.
SECURITY_CSRF_COOKIE = {"key": "XSRF-TOKEN"}
WTF_CSRF_CHECK_DEFAULT = False
WTF_CSRF_TIME_LIMIT = None