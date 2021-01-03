from datetime import datetime, timedelta
import unittest

from app import create_app, db
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

# Put tests here

if __name__ == '__main__':
    unittest.main(verbosity=2)