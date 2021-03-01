"""Module containing the Extract model and supporting functionality."""

import collections
import csv
from datetime import datetime
import json
import os
import pathlib
import tempfile
import typing
from uuid import uuid4
import zipfile

from flask import current_app, url_for

from searchtweets import convert_utc_time

from ..extensions import db
from .tweet_providers import get_tweets_by_id, get_tweets_by_search, save_to_redis
from .plugins import PluginCollection
from .tools import ContextProxyLogger


# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)


__all__ = [
    'Extract',
]


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

    #: user_id of person who requested the Bundle
    user_id = db.Column(db.Unicode(16), index=True, nullable=True)

    #: Should the bundle be limited to only the user who requested it
    validate_on_email = db.Column(db.Boolean, default=False)

    #: Is the Bundle ready for pickup?
    ready = db.Column(db.Boolean, default=False, index=True, nullable=False)

    #: Details the method
    extract_method = db.Column(db.String(254), default="", nullable=False)

    def save(self) -> None:
        """Save this model to the database."""
        db.session.add(self)
        db.session.commit()

    def build(self, query, twitter_key_dict, **kwargs):
        """Build a requested Twitter extract.

        Called by `extract.tasks.build_extract` Celery task.

        :param query: depending on the defined extract method this will contain:
                      extract.method == ID: Tweet IDs to include within this Bundle.
                      extract.method == Search: A search query string to be processed and **kwargs will be populated
                      with keyword arguments
        """

        logger.info(f'Processing Bundle {self.uuid}, using method {self.extract_method}')
        if self.extract_method == "ID":
            tweets = get_tweets_by_id(query,
                                      twitter_key_dict=twitter_key_dict,
                                      tweet_providers=current_app.config['TWEET_PROVIDERS'])
        elif self.extract_method == "Search":
            logger.info(f"{kwargs}")
            additional_search_settings = {
                'results_per_call': 10,
                'max_results': 10,
                'start_time': "1d",
                'end_time': "10m",
                'since_id': None,
                'until_id': None,
                'tweet_fields': None,
                'user_fields': None,
                'media_fields': None,
                'place_fields': None,
                'poll_fields': None,
                'expansions': None,
                'stringify': True
            }

            for key in kwargs.keys():
                if key in list(additional_search_settings.keys()):
                    additional_search_settings[key] = kwargs[key]
            logger.info(f"{additional_search_settings}")
            # check there are not parameter conflicts
            assert int(additional_search_settings['results_per_call']) > 9,\
                f"results_per_call (={additional_search_settings['results_per_call']})  must be >= 10"
            if additional_search_settings['since_id'] is not None:
                assert additional_search_settings['start_time'] is None, \
                    "'Tweet ID from' and 'Date from' cannot both be set"
            if additional_search_settings['until_id'] is not None:
                assert additional_search_settings['end_time'] is None, \
                    "'Tweet ID to' and 'Date to' cannot both be set"
            if (additional_search_settings['since_id'] is not None) \
                and \
                    (additional_search_settings['until_id'] is not None):
                assert additional_search_settings['since_id'] < additional_search_settings['until_id'], \
                    "'Tweet ID to' must be greater than 'Tweet ID from'"
            if (additional_search_settings['start_time'] is not None) \
                and \
                    (additional_search_settings['end_time'] is not None):
                assert compare_time(additional_search_settings['start_time'],
                                    additional_search_settings['end_time']), \
                       "'Date to' must be after 'Date from'"
            tweets = get_tweets_by_search(query,
                                          twitter_key_dict,
                                          additional_search_settings,
                                          current_app.config['TWEET_PROVIDERS_V2'])
        try:
            save_to_redis(tweets)
        except ConnectionError as exc:
            current_app.logger.error('Failed to cache found Tweets: %s', exc)

        with tempfile.TemporaryDirectory() as tmp_dir:
            work_dir = pathlib.Path(tmp_dir)
            query_file_txt = work_dir.joinpath('search_query.txt')
            search_returns_json = work_dir.joinpath('search_fields.json')
            tweets_file_json = work_dir.joinpath('tweets.json')
            tweets_file_csv = work_dir.joinpath('tweets.csv')

            with open(tweets_file_json, mode='w', encoding='utf-8') as json_out:
                json.dump(tweets, json_out, ensure_ascii=False, indent=4)
                current_app.logger.info(f'Tweets saved to json')
            with open(tweets_file_csv, mode='w', newline='') as csv_out:
                fieldnames = ['id', 'conservation_id', 'author_id', 'text', 'created_at', 'lang',
                              'public_metrics_retweet_count', 'public_metrics_reply_count',
                              'public_metrics_like_count', 'public_metrics_quote_count']
                csv_writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
                csv_writer.writeheader()
                for tweet in tweets:
                    flat_tweet = flatten(tweet)
                    abridged_tweet = {key: flat_tweet.get(key, "") for key in fieldnames}
                    csv_writer.writerow(abridged_tweet)
                current_app.logger.info(f'Tweets saved to csv')
            with open(search_returns_json, mode='w', encoding='utf-8') as search_out:
                json.dump(additional_search_settings, search_out, ensure_ascii=False, indent=4)
                current_app.logger.info(f'Return fields saved')
            with open(query_file_txt, mode='w') as query_out:
                query_out.write(query)
                current_app.logger.info(f'API query saved')

            """for plugin in get_plugins().values():
                output = plugin(tweets_file_json, tmp_dir, twitter_key_dict)
                current_app.logger.info(f'Plugin output: {output}')"""

            zip_path = current_app.config['OUTPUT_DIR'].joinpath(self.uuid).with_suffix('.zip')
            zip_directory(zip_path, work_dir)
            current_app.logger.info('Zipped output files to %s', zip_path)

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
        for root, _, files in os.walk(dir_path):
            for f in files:  # pylint: disable=invalid-name
                filepath = pathlib.Path(root, f)
                z.write(filepath, arcname=filepath.relative_to(dir_path))


def get_plugins() -> typing.Dict[pathlib.Path, typing.Callable]:
    """Get list of plugin classes."""
    plugin_directories = [
        current_app.config['PLUGIN_DIR'],
    ]
    return PluginCollection(plugin_directories).load_plugins()


def compare_time(start, end):
    """ Compute is end is after start from the time parameters to be passed to the twitter API by passing though UTC"""
    start_utc = convert_utc_time(start)
    end_utc = convert_utc_time(end)
    return datetime.strptime(start_utc, '%Y-%m-%dT%H:%M:%SZ') < datetime.strptime(end_utc, '%Y-%m-%dT%H:%M:%SZ')


def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
