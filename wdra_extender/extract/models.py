"""Module containing the Extract model and supporting functionality."""

import datetime
import logging
import json
import os
import pathlib
import tempfile
import time
import typing
from uuid import uuid4
import zipfile

from flask import current_app, url_for
from twarc import Twarc
import redis

from ..extensions import db

__all__ = [
    'Extract',
]

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Extract(db.Model):
    """A Twitter Extract Bundle.

    A Twitter Extract Bundle is a collection of files produced by the Twitter
    data analysis scripts from a list of Tweet ids.
    """
    # pylint: disable=no-member

    #: UUID identifier for the Bundle - acts as PK
    uuid = db.Column(db.String(36),
                     default=lambda: str(uuid4()),
                     index=True,
                     nullable=False,
                     primary_key=True,
                     unique=True)

    #: Email address of person who requested the Bundle
    email = db.Column(db.String(254), index=True, nullable=False)

    #: Is the Bundle ready for pickup?
    ready = db.Column(db.Boolean, default=False, index=True, nullable=False)

    def save(self) -> None:
        """Save this model to the database."""
        db.session.add(self)
        db.session.commit()

    def build(self, tweet_ids):
        """Build a requested Twitter extract.

        Called by `extract.tasks.build_extract` Celery task.

        :param tweet_ids: Tweet IDs to include within this Bundle.
        """
        logger.info('Processing Bundle %s', self.uuid)

        tweets = get_tweets(tweet_ids)
        with tempfile.TemporaryDirectory() as tmp_dir:
            work_dir = pathlib.Path(tmp_dir)
            tweets_file = work_dir.joinpath('tweets.json')
            with open(tweets_file, mode='w', encoding='utf-8') as f:
                json.dump(tweets, f, ensure_ascii=False, indent=4)

            for plugin_name, plugin in get_plugins().items():
                output = plugin(tweets=tweets,
                                tweets_file=tweets_file,
                                work_dir=tmp_dir)
                logger.info(output)

            zip_path = current_app.config['OUTPUT_DIR'].joinpath(
                self.uuid).with_suffix('.zip')
            zip_directory(zip_path, work_dir)
            logger.info('Zipped output files to %s', zip_path)

        self.ready = True
        self.save()
        return self.uuid

    def get_absolute_url(self):
        """Get the URL for this object's detail view."""
        return url_for('extract.download_extract', extract_uuid=self.uuid)


def zip_directory(zip_path: pathlib.Path, dir_path: pathlib.Path):
    """Create a zipfile from a directory."""
    if not dir_path.is_dir():
        raise NotADirectoryError

    with zipfile.ZipFile(zip_path, 'w') as z:
        for root, dirs, files in os.walk(dir_path):
            for f in files:
                filepath = pathlib.Path(root, f)
                z.write(filepath, arcname=filepath.relative_to(dir_path))


def get_plugins() -> typing.Dict[pathlib.Path, typing.Callable]:
    """Get list of plugin classes."""
    from .plugins.base import PluginCollection

    plugin_directories = [
        current_app.config['BASE_DIR'].joinpath('plugins-enabled'),
    ]
    return PluginCollection(plugin_directories).load_plugins()


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
