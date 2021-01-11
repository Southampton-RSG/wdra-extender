"""Module containing views related to Twitter Extract Bundles."""

import pathlib
import typing

from flask import Blueprint, current_app, render_template, redirect, request, send_from_directory
import werkzeug

from . import models, tasks

blueprint_extract_method = Blueprint("extract_method", __name__,
                                     url_prefix='/extract_method')  # pylint: disable=invalid-name
blueprint_extract_id = Blueprint("extract_id", __name__,
                                 url_prefix='/extract_ids')  # pylint: disable=invalid-name
blueprint_extract_search = Blueprint("extract_search", __name__,
                                     url_prefix='/extract_search')  # pylint: disable=invalid-name
blueprint_extract_rep = Blueprint("extract_rep", __name__,
                                  url_prefix='/extract_rep')  # pylint: disable=invalid-name


class ValidationError(werkzeug.exceptions.BadRequest):
    """Error in validating user-provided data."""
    code = 400
    description = 'Invalid data provided.'


def cast_tweet_id(tweet_id: str) -> int:
    """Cast a single Tweet ID to int.

    They may be prefixed with 'ID:' so try to remove this.
    """
    if tweet_id.lower().startswith('id:'):
        tweet_id = tweet_id.lower()[3:]

    return int(tweet_id)


def validate_tweet_ids(tweet_ids: typing.Iterable[str]) -> typing.List[int]:
    """Cast Tweet IDs to integer or raise ValidationError."""

    if not tweet_ids:
        raise ValidationError('No Tweet IDs were found.')

    try:
        # Filter out blank lines and cast to int
        return [cast_tweet_id(tweet_id) for tweet_id in tweet_ids if tweet_id.strip()]

    except ValueError as exc:
        raise ValidationError('Tweet IDs must be integers.') from exc


@blueprint_extract_method.route('/', methods=['POST'])
def select_method():
    """View to select the extract method"""
    extract_method_names = ['Search', 'ID', 'Replication']
    extract_methods = {
        'Search': get_by_search,
        'ID': request_extract,
        'Replication': get_by_replication
    }
    return redirect(extract_methods[request.form['method_select']].get_absolute_url())


@blueprint_extract_rep.route('/', methods=['POST'])
def get_by_replication():
    ""
    return None


@blueprint_extract_search.route('/', methods=['POST'])
def get_by_search():
    # stuff
    return None


@blueprint_extract_id.route('/', methods=['POST'])
def request_extract():
    """View to request a Twitter Extract Bundle."""
    tweet_ids = request.form['tweet_ids'].splitlines()
    tweet_ids = validate_tweet_ids(tweet_ids)

    extract = models.Extract(email=request.form['email'])
    extract.save()

    if current_app.config['CELERY_BROKER_URL']:
        # Add job to task queue
        tasks.build_extract.delay(extract.uuid, tweet_ids)

    else:
        # Build the extract now
        extract.build(tweet_ids)

    return redirect(extract.get_absolute_url())


@blueprint_extract_id.route('/<uuid:extract_uuid>')
def detail_extract(extract_uuid):
    """View displaying details of a Twitter Extract Bundle."""
    extract = models.Extract.query.get(str(extract_uuid))

    return render_template('extract.html', extract=extract)


@blueprint_extract_id.route('/<uuid:extract_uuid>/fetch')
def download_extract(extract_uuid):
    """View to download a Twitter Extract Bundle."""
    return send_from_directory(current_app.config['OUTPUT_DIR'],
                               pathlib.Path(
                                   str(extract_uuid)).with_suffix('.zip'),
                               as_attachment=True)
