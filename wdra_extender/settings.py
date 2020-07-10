"""Project settings file.

Gets settings from .env or settings.ini file.
"""

import pathlib

from decouple import AutoConfig

BASE_DIR = pathlib.Path(__name__).absolute().parent
config = AutoConfig(search_path=str(BASE_DIR))

#: Directory into which output zip files should be placed
OUTPUT_DIR = config('OUTPUT_DIR',
                    cast=pathlib.Path,
                    default=BASE_DIR.joinpath('media'))

REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', cast=int, default=6379)
REDIS_DB = config('REDIS_DB', default='0')

CELERY_BROKER_URL = config(
    'CELERY_BROKER_URL',
    default=f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')

SQLALCHEMY_DATABASE_URI = config(
    'SQLALCHEMY_DATABASE_URI',
    default=f'sqlite:///{BASE_DIR.joinpath("db.sqlite3")}')

TWITTER_CONSUMER_KEY = config('TWITTER_CONSUMER_KEY')
TWITTER_CONSUMER_SECRET = config('TWITTER_CONSUMER_SECRET')

# TWITTER_ACCESS_TOKEN = config('TWITTER_ACCESS_TOKEN')
# TWITTER_ACCESS_TOKEN_SECRET = config('TWITTER_ACCESS_TOKEN_SECRET')

SQLALCHEMY_TRACK_MODIFICATIONS = False
