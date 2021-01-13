"""Config options for WDRAX.

Gets settings from environment variables or .env/settings.ini file.
"""

import pathlib

from decouple import AutoConfig
import yaml

BASE_DIR = pathlib.Path(__name__).absolute().parent
config = AutoConfig(search_path=str(BASE_DIR))  # pylint: disable=invalid-name

PLUGIN_DIR = config('PLUGIN_DIR',
                    cast=pathlib.Path,
                    default=BASE_DIR.joinpath('plugins'))

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
BEARER_TOKEN = config('BEARER_TOKEN', default=None)

# Make a yaml file for search_tweets_v2,
# Docs to add extra config and endpoints https://github.com/twitterdev/search-tweets-python/tree/v2#yaml-method
dict_file = [{'get_tweets': {'endpoint': 'https://api.twitter.com/2/tweets/',
                             'consumer_key': f'{TWITTER_CONSUMER_KEY}',
                             'consumer_secret': f'{TWITTER_CONSUMER_SECRET}',
                             'bearer_token': f'{BEARER_TOKEN}'},
              'search_tweets': {'endpoint': 'https://api.twitter.com/2/tweets/search/recent',
                                'consumer_key': f'{TWITTER_CONSUMER_KEY}',
                                'consumer_secret': f'{TWITTER_CONSUMER_SECRET}',
                                'bearer_token': f'{BEARER_TOKEN}'},
              'user_mention': {'endpoint': 'https://api.twitter.com/2/users/:id/mentions',
                               'consumer_key': f'{TWITTER_CONSUMER_KEY}',
                               'consumer_secret': f'{TWITTER_CONSUMER_SECRET}',
                               'bearer_token': f'{BEARER_TOKEN}'},
              'user_tweets': {'endpoint': 'https://api.twitter.com/2/users/:id/tweet',
                              'consumer_key': f'{TWITTER_CONSUMER_KEY}',
                              'consumer_secret': f'{TWITTER_CONSUMER_SECRET}',
                              'bearer_token': f'{BEARER_TOKEN}'},
              }
             ]

with open(BASE_DIR.joinpath('.twitter_keys.yaml'), 'w') as file:
    documents = yaml.dump(dict_file, file)

SQLALCHEMY_TRACK_MODIFICATIONS = False
