"""Project settings file.

Gets settings from .env or settings.ini file.
"""

import pathlib

from decouple import AutoConfig

BASE_DIR = pathlib.Path(__name__).absolute().parent
config = AutoConfig(search_path=str(BASE_DIR))

CELERY_BROKER_URL = config('CELERY_BROKER_URL',
                           default='redis://localhost:6379/0')

SQLALCHEMY_DATABASE_URI = config('SQLALCHEMY_DATABASE_URI',
                                 default='sqlite:///../db.sqlite3')

TWITTER_CONSUMER_KEY = config('TWITTER_CONSUMER_KEY')
TWITTER_CONSUMER_SECRET = config('TWITTER_CONSUMER_SECRET')

# TWITTER_ACCESS_TOKEN = config('TWITTER_ACCESS_TOKEN')
# TWITTER_ACCESS_TOKEN_SECRET = config('TWITTER_ACCESS_TOKEN_SECRET')

SQLALCHEMY_TRACK_MODIFICATIONS = False
