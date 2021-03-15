"""Config options for WDRAX.

Gets settings from environment variables or .env/settings.ini file.
"""
import os
import pathlib

from decouple import AutoConfig
import yaml

# Use the parent directory as the root relative to which we define other paths
BASE_DIR = pathlib.Path(__name__).absolute().parent

# read settings.ini for local configuration
config = AutoConfig(search_path=str(BASE_DIR))  # pylint: disable=invalid-name

# Logging settings
LOG_LEVEL = config('LOG_LEVEL', default='INFO')

# Security key
SECRET_KEY = os.urandom(16)

# Directory where executable analysis scrips are stored
PLUGIN_DIR = config('PLUGIN_DIR',
                    cast=pathlib.Path,
                    default=BASE_DIR.joinpath('plugins'))

# Directory into which output zip files are placed ready for download
OUTPUT_DIR = config('OUTPUT_DIR',
                    cast=pathlib.Path,
                    default=BASE_DIR.joinpath('media'))

# configure the redis database
REDIS_HOST = config('REDIS_HOST', default=None)
REDIS_PORT = config('REDIS_PORT', cast=int, default=6379)
REDIS_DB = config('REDIS_DB', default='0')

# Configure the job runner
CELERY_BROKER_URL = config(
    'CELERY_BROKER_URL',
    default=(None if REDIS_HOST is None else
             f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'))

CELERY_RESULT_BACKEND = config(
    'CELERY_RESULT_BACKEND',
    default=CELERY_BROKER_URL
)

CELERY_IMPORTS = config(
    'CELERY_IMPORTS',
    default=("wdra_extender.tasks", )
)

# User session settings
SESSION_TYPE = 'redis'
SESSION_REDIS = config(
    'SESSION REDIS',
    default=(None if REDIS_HOST is None else
             f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'))
SESSION_COOKIE_NAME = 'wdrax_session'
SESSION_USE_SIGNER = True

# Define the SQL Alchemy configuration for the extract and user model tables.
SQLALCHEMY_DATABASE_URI = config('DATABASE_URL')  # From settings.ini
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Login extension settings
REMEMBER_COOKIE_NAME = 'wdrax_user'

# Define where to get the tweets from and define null environment variables for storing twitter credentials that can be=
# loaded later with user credentials ===================================================================================

# Null credentials to be assigned at runtime by the user
TWITTER_CONSUMER_KEY = config('TWITTER_CONSUMER_KEY', default=None)
TWITTER_CONSUMER_SECRET = config('TWITTER_CONSUMER_SECRET', default=None)
TWITTER_ACCESS_TOKEN = config('TWITTER_ACCESS_TOKEN', default=None)
TWITTER_ACCESS_TOKEN_SECRET = config('TWITTER_ACCESS_TOKEN_SECRET', default=None)
BEARER_TOKEN = config('BEARER_TOKEN', cast=str, default=None)

# API for version one using Twarc as the provider and Redis to retrieve from the local database
TWEET_PROVIDERS = [
    'wdra_extender.extract.tweet_providers.redis_provider',
    'wdra_extender.extract.tweet_providers.twarc_provider',
]

# Searchtweets is a Beta V2 provider which will be updated to include all available endpoints.
# This will eventually deprecate twarc.
TWEET_PROVIDERS_V2 = [
    'wdra_extender.extract.tweet_providers.searchtweets_provider',
]

# Make a yaml file for search_tweets_v2,
# Docs to add extra config and endpoints https://github.com/twitterdev/search-tweets-python/tree/v2#yaml-method
dict_file = {'get_tweets_by_id': {'endpoint': 'https://api.twitter.com/2/tweets/',
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

# This is blank and currently never used to overwrite user credentials but could be used to provide a framework for ====
# organisational logins or local installs
with open(BASE_DIR.joinpath('.twitter_keys.yaml'), 'w') as file:
    documents = yaml.dump(dict_file, file)
TWITTER_CONF = BASE_DIR.joinpath('.twitter_keys.yaml')

# This defines the return fields that can be selected as part of the twitter extract bundle. This could in theory be ===
# automatically extracted from the twitter api?
TWITTER_RETURN_DICT = {'tweet_fields': ['attachments',
                                        'author_id',
                                        'context_annotations',
                                        'conversation_id',
                                        'created_at',
                                        'entities',
                                        'geo',
                                        'id',
                                        'in_reply_to_user_id',
                                        'lang',
                                        'public_metrics',
                                        'possibly_sensitive',
                                        'poll_fields',
                                        'referenced_tweets',
                                        'reply_settings',
                                        'source',
                                        'text',
                                        'withheld'],
                       'attachments': ['duration_ms',
                                       'height',
                                       'media_key',
                                       'preview_image_url',
                                       'type',
                                       'url',
                                       'width',
                                       'public_metrics',
                                       'non_public_metrics',
                                       'organic_metrics',
                                       'promoted_metrics'],  # Real name media.fields
                       'author_id':   ['created_at',
                                       'description',
                                       'entities',
                                       'id',
                                       'location',
                                       'name',
                                       'pinned_tweet_id',
                                       'profile_image_url',
                                       'protected',
                                       'public_metrics',
                                       'url',
                                       'username',
                                       'verified',
                                       'withheld'],  # Real name user.fields
                       'poll_fields': ['duration_minutes',
                                       'end_datetime',
                                       'id',
                                       'options',
                                       'voting_status'],  # Real name poll.fields
                       'geo': ['contained_within',
                               'country',
                               'country_code',
                               'full_name',
                               'geo',
                               'id',
                               'name',
                               'place_type'],  # Real name place.fields
                       'id': ['attachments.poll_ids',
                              'attachments.media_keys',
                              'author_id',
                              'entities.mentions.username',
                              'geo.place_id',
                              'in_reply_to_user_id',
                              'referenced_tweets.id',
                              'referenced_tweets.id.author_id']  # Real name expansions
                       }

