"""Project settings file.

Gets settings from .env or settings.ini file.
"""

import pathlib

from decouple import config

BASE_DIR = pathlib.Path(__name__).parent

CELERY_BROKER_URL = config('CELERY_BROKER_URL',
                           default='pyamqp://wdra:wdra@localhost:5672/wdra')

SQLALCHEMY_DATABASE_URI = config('SQLALCHEMY_DATABASE_URI',
                                 default='sqlite:///../db.sqlite3')

SQLALCHEMY_TRACK_MODIFICATIONS = False
