import datetime
import json
import logging
import time
import typing

from flask import current_app

import redis
from twarc import Twarc

__all__ = [
    'get_tweets',
]

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def get_tweets(tweet_ids: typing.Iterable[int]) -> typing.List[typing.Mapping]:
    """Get a list of Tweets from their IDs.

    First check for Tweets which have been cached, then collect uncached Tweets from the Twitter API.
    """
    config = current_app.config
    r = redis.Redis(  # pylint: disable=invalid-name
        host=config['REDIS_HOST'],
        port=config['REDIS_PORT'],
        db=config['REDIS_DB'])

    uncached_tweet_ids = []
    cached_tweets = []

    # Attempt to get all Tweets from cache
    get_redis_key = lambda i: f'tweet_hydrated:{i}'
    for tweet_id, tweet_string in zip(tweet_ids,
                                      r.mget(map(get_redis_key, tweet_ids))):

        if tweet_string is None:
            uncached_tweet_ids.append(tweet_id)

        else:
            cached_tweets.append(json.loads(tweet_string))

    logger.info('Found %d cached Tweets', len(cached_tweets))

    if uncached_tweet_ids:
        logger.info('Fetching %d uncached Tweets', len(uncached_tweet_ids))
        # Twitter API consumer - handles rate limits for us
        t = Twarc(  # pylint: disable=invalid-name
            current_app.config['TWITTER_CONSUMER_KEY'],
            current_app.config['TWITTER_CONSUMER_SECRET'])

        time.sleep(10)

        # Get data for Tweets not in cache
        # Then put them in the cache
        for tweet in t.hydrate(uncached_tweet_ids):
            redis_key = get_redis_key(tweet['id'])
            redis_value = json.dumps(tweet)
            r.setex(redis_key, datetime.timedelta(days=10), redis_value)

            cached_tweets.append(tweet)

    return cached_tweets