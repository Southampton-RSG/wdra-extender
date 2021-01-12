"""Module containing the Extract model and supporting functionality."""

import logging
import json
import os
import pathlib
import tempfile
import typing
from uuid import uuid4
import zipfile

from flask import current_app, url_for

from ..extensions import db
from .tweet_providers import get_tweets, save_to_redis
from .plugins import PluginCollection

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

    extract_method = db.Column(db.String(254), default=None, index=True)

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
        tweets = get_tweets(self.extract_method,
            tweet_ids, tweet_providers=current_app.config['TWEET_PROVIDERS'])

        try:
            save_to_redis(tweets)
        except ConnectionError as exc:
            logger.error('Failed to cache found Tweets: %s', exc)

        with tempfile.TemporaryDirectory() as tmp_dir:
            work_dir = pathlib.Path(tmp_dir)
            tweets_file = work_dir.joinpath('tweets.json')

            with open(tweets_file, mode='w', encoding='utf-8') as json_out:
                json.dump(tweets, json_out, ensure_ascii=False, indent=4)

            for plugin in get_plugins().values():
                output = plugin(tweets_file, tmp_dir)
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
        return url_for('extract.detail_extract', extract_uuid=self.uuid)


def zip_directory(zip_path: pathlib.Path, dir_path: pathlib.Path):
    """Create a zipfile from a directory."""
    if not dir_path.is_dir():
        raise NotADirectoryError

    with zipfile.ZipFile(zip_path, 'w') as z:  # pylint: disable=invalid-name
        for root, dirs, files in os.walk(dir_path):
            for f in files:  # pylint: disable=invalid-name
                filepath = pathlib.Path(root, f)
                z.write(filepath, arcname=filepath.relative_to(dir_path))


def get_plugins() -> typing.Dict[pathlib.Path, typing.Callable]:
    """Get list of plugin classes."""
    plugin_directories = [
        current_app.config['PLUGIN_DIR'],
    ]
    return PluginCollection(plugin_directories).load_plugins()
