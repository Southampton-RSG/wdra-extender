"""Config options for WDRAX.

Gets settings from environment variables or .env/settings.ini file.
"""

import pathlib

from decouple import AutoConfig

BASE_DIR = pathlib.Path(__name__).absolute().parent
config = AutoConfig(search_path=str(BASE_DIR))  # pylint: disable=invalid-name

PLUGIN_DIR = config('PLUGIN_DIR',
                    cast=pathlib.Path,
                    default=BASE_DIR.joinpath('plugins-enabled'))

#: Directory into which output zip files should be placed
OUTPUT_DIR = config('OUTPUT_DIR',
                    cast=pathlib.Path,
                    default=BASE_DIR.joinpath('media'))

REDIS_HOST = config('REDIS_HOST', default=None)
REDIS_PORT = config('REDIS_PORT', cast=int, default=6379)
REDIS_DB = config('REDIS_DB', default='0')

CELERY_BROKER_URL = config(
    'CELERY_BROKER_URL',
    default=(None if REDIS_HOST is None else
             f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'))

SQLALCHEMY_DATABASE_URI = config(
    'SQLALCHEMY_DATABASE_URI',
    default=f'sqlite:///{BASE_DIR.joinpath("db.sqlite3")}')

TWEET_PROVIDERS = [
    'wdra_extender.extract.tweet_providers.redis_provider',
    'wdra_extender.extract.tweet_providers.twarc_provider',
]

TWITTER_CONSUMER_KEY = config('TWITTER_CONSUMER_KEY', default=None)
TWITTER_CONSUMER_SECRET = config('TWITTER_CONSUMER_SECRET', default=None)
TWITTER_ACCESS_TOKEN = config('TWITTER_ACCESS_TOKEN', default=None)
TWITTER_ACCESS_TOKEN_SECRET = config('TWITTER_ACCESS_TOKEN_SECRET', default=None)

SQLALCHEMY_TRACK_MODIFICATIONS = False
