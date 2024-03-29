import datetime
import importlib
import json
import logging
import typing

from flask import current_app
import redis
from twarc import Twarc

__all__ = [
    'get_tweets',
    'redis_provider',
    'twarc_provider',
]


class ContextProxyLogger(logging.Logger):
    """Logger proxy for when we may be inside or outside of the Flask context.

    If inside the Flask context, redirect to the Flask app logger.
    If outside the Flask context, act as a default Python logger.
    """
    def __getattribute__(self, name: str) -> typing.Any:
        try:
            return current_app.logger.__getattribute__(name)

        except RuntimeError as exc:
            if 'outside of application context' in str(exc):
                return super().__getattribute__(name)

            raise


# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)


def import_object(name: str) -> object:
    """Get a single object from a module."""
    module_name, object_name = name.rsplit('.', 1)

    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def get_tweets(
        tweet_ids: typing.Iterable[int],
        tweet_providers: typing.Iterable[str]) -> typing.List[typing.Mapping]:
    """Get a list of Tweets from their IDs.

    Attempt to get tweets from each of the tweet providers in turn.
    Tweet providers should be passed as the importable name of the callable.
    e.g. 'wdra_extender.extract.tweet_providers.redis_provider'

    :param tweet_ids: Tweet IDs to lookup.
    :param tweet_providers: Iterable of names of tweet provider functions to import.
    """
    tweet_ids = set(tweet_ids)
    found_tweets = []

    for provider in map(import_object, tweet_providers):
        try:
            provider_found_ids, provider_found_tweets = provider(tweet_ids)

        except ConnectionError as exc:
            logger.error('Failed to execute Tweet provider: %s', exc)

        else:
            found_tweets.extend(provider_found_tweets)
            tweet_ids -= provider_found_ids
            logger.info(
                f'Found {len(provider_found_ids)} tweets using provider \'{provider.__name__}\''
            )

        if tweet_ids:
            logger.info(f'There are {len(tweet_ids)} tweets left to find')

        else:
            logger.info('Found all tweets - skipping remaining providers')
            break

    return found_tweets


def save_to_redis(
    tweets: typing.List[typing.Mapping],
    cache_time: datetime.timedelta = datetime.timedelta(days=10)
) -> None:
    """Save tweet JSON to Redis cache."""
    config = current_app.config
    r = redis.Redis(  # pylint: disable=invalid-name
        host=config['REDIS_HOST'],
        port=config['REDIS_PORT'],
        db=config['REDIS_DB'])

    # Pipeline executes all commands in a single request
    pipe = r.pipeline()
    for tweet in tweets:
        redis_key = f'tweet_hydrated:{tweet["id"]}'
        redis_value = json.dumps(tweet)
        # There is no MSETEX command to do this in one request without a pipeline
        pipe.setex(redis_key, cache_time, redis_value)

    try:
        pipe.execute()

    except redis.exceptions.ConnectionError as exc:
        raise ConnectionError from exc


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
    try:
        tweets = r.mget(map(lambda i: f'tweet_hydrated:{i}', tweet_ids))

    except redis.exceptions.ConnectionError as exc:
        raise ConnectionError from exc

    for tweet_id, tweet_string in zip(tweet_ids, tweets):
        if tweet_string is not None:
            found_tweet_ids.add(tweet_id)
            found_tweets.append(json.loads(tweet_string))

    return found_tweet_ids, found_tweets


def twarc_provider(
    tweet_ids: typing.Iterable[int]
) -> typing.Tuple[typing.Set[int], typing.List[typing.Mapping]]:
    """Get a list of Tweets from their IDs sourced from the Twitter API.

    Uses Twarc Twitter API connector - https://github.com/DocNow/twarc.
    """
    # Twitter API consumer - handles rate limits for us
    t = Twarc(  # pylint: disable=invalid-name
        consumer_key=current_app.config['TWITTER_CONSUMER_KEY'],
        consumer_secret=current_app.config['TWITTER_CONSUMER_SECRET'],
        access_token=current_app.config['TWITTER_ACCESS_TOKEN'],
        access_token_secret=current_app.config['TWITTER_ACCESS_TOKEN_SECRET'],
    )

    found_tweets = list(t.hydrate(tweet_ids))
    found_tweet_ids = {tweet['id'] for tweet in found_tweets}

    return found_tweet_ids, found_tweets
