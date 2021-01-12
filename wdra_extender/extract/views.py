"""Module containing views related to Twitter Extract Bundles."""
import pathlib
import typing

from flask import Blueprint, current_app, render_template, redirect, request, send_from_directory, url_for
import werkzeug

from . import models, tasks


blueprint_extract = Blueprint("extract", __name__,
                              url_prefix='/extract')


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


@blueprint_extract.route('/', methods=['POST'])
def extract_email():
    """View to get the user email and create a uuid"""
    extract = models.Extract(email=request.form['email'])
    extract.save()
    return redirect(url_for('extract.select_method', extract_uuid=extract.uuid))


@blueprint_extract.route('/method/<uuid:extract_uuid>', methods=['GET', 'POST'])
def select_method(extract_uuid):
    """View to select the extract method"""
    extract_methods = {
        'Search': 'extract.get_by_search',
        'ID': 'extract.get_by_id',
        'Replication': 'extract.get_by_replication'
    }

    if request.method == "POST":
        selected = request.form.get('method_select')
        return redirect(url_for(extract_methods[selected], extract_uuid=extract_uuid))
    else:
        return render_template('get_method.html', extract_methods=extract_methods, extract_uuid=extract_uuid)


@blueprint_extract.route('/method/replication/<uuid:extract_uuid>', methods=['POST'])
def get_by_replication(extract_uuid):
    """"""
    return None


@blueprint_extract.route('/method/search/<uuid:extract_uuid>', methods=['POST'])
def get_by_search(extract_uuid):
    # stuff
    return None


@blueprint_extract.route('/method/id/<uuid:extract_uuid>', methods=['GET', 'POST'])
def get_by_id(extract_uuid):
    """View to request a Twitter Extract Bundle."""

    if request.method == "POST":
        extract = models.Extract.query.get(str(extract_uuid))
        tweet_ids = request.form['tweet_ids'].splitlines()
        tweet_ids = validate_tweet_ids(tweet_ids)

        if current_app.config['CELERY_BROKER_URL']:
            # Add job to task queue
            tasks.build_extract.delay(extract.uuid, tweet_ids)
        else:
            # Build the extract now
            extract.build(tweet_ids)

        return redirect(extract.get_absolute_url())
    else:
        return render_template('get_by_id.html', extract_uuid=extract_uuid)


@blueprint_extract.route('/detail/<uuid:extract_uuid>')
def detail_extract(extract_uuid):
    """View displaying details of a Twitter Extract Bundle."""
    extract = models.Extract.query.get(str(extract_uuid))

    return render_template('extract.html', extract=extract)


@blueprint_extract.route('/download/<uuid:extract_uuid>/fetch')
def download_extract(extract_uuid):
    """View to download a Twitter Extract Bundle."""
    return send_from_directory(current_app.config['OUTPUT_DIR'],
                               pathlib.Path(
                                   str(extract_uuid)).with_suffix('.zip'),
                               as_attachment=True)
