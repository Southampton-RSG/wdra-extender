import datetime
import importlib
import json
import logging
import time
import typing

from flask import current_app
import redis
from twarc import Twarc

from ..settings import TWEET_PROVIDERS

__all__ = [
    'get_tweets',
    'redis_provider',
    'twarc_provider',
]

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def import_object(name: str) -> object:
    """Get a single object from a module."""
    module_name, object_name = name.rsplit('.', 1)

    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def get_tweets(tweet_ids: typing.Iterable[int]) -> typing.List[typing.Mapping]:
    """Get a list of Tweets from their IDs.

    First check for Tweets which have been cached, then collect uncached Tweets from the Twitter API.
    """
    tweet_ids = set(tweet_ids)
    found_tweets = []

    for provider in map(import_object, TWEET_PROVIDERS):
        provider_found_ids, provider_found_tweets = provider(tweet_ids)

        found_tweets.extend(provider_found_tweets)
        tweet_ids -= provider_found_ids
        if not tweet_ids:
            logger.info('Found all tweets - skipping remaining providers')
            break

    return found_tweets


def redis_provider(
    tweet_ids: typing.Iterable[int]
) -> typing.Tuple[typing.List[int], typing.List[typing.Mapping]]:
    config = current_app.config
    r = redis.Redis(  # pylint: disable=invalid-name
        host=config['REDIS_HOST'],
        port=config['REDIS_PORT'],
        db=config['REDIS_DB'])

    found_tweet_ids = set()
    found_tweets = []

    # Attempt to get all Tweets from cache
    get_redis_key = lambda i: f'tweet_hydrated:{i}'
    for tweet_id, tweet_string in zip(tweet_ids,
                                      r.mget(map(get_redis_key, tweet_ids))):

        if tweet_string is not None:
            found_tweet_ids.add(tweet_id)

        else:
            found_tweets.append(json.loads(tweet_string))

    logger.info('Found %d cached Tweets', len(found_tweet_ids))

    return found_tweet_ids, found_tweets


def twarc_provider(
    tweet_ids: typing.Iterable[int]
) -> typing.Tuple[typing.Set[int], typing.List[typing.Mapping]]:
    """Get a list of Tweets from their IDs.

    First check for Tweets which have been cached, then collect uncached Tweets from the Twitter API.
    """
    config = current_app.config
    r = redis.Redis(  # pylint: disable=invalid-name
        host=config['REDIS_HOST'],
        port=config['REDIS_PORT'],
        db=config['REDIS_DB'])

    logger.info('Fetching %d uncached Tweets', len(tweet_ids))
    # Twitter API consumer - handles rate limits for us
    t = Twarc(  # pylint: disable=invalid-name
        current_app.config['TWITTER_CONSUMER_KEY'],
        current_app.config['TWITTER_CONSUMER_SECRET'])

    time.sleep(10)

    # Get data for Tweets not in cache
    # Then put them in the cache
    found_tweet_ids = set()
    found_tweets = []
    for tweet in t.hydrate(tweet_ids):
        redis_key = f'tweet_hydrated:{tweet["id"]}'
        redis_value = json.dumps(tweet)
        r.setex(redis_key, datetime.timedelta(days=10), redis_value)

        found_tweet_ids.add(tweet['id'])
        found_tweets.append(tweet)

    return found_tweet_ids, found_tweets