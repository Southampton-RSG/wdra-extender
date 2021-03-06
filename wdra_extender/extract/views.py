"""Module containing views related to Twitter Extract Bundles."""
import typing

from flask import Blueprint, render_template, redirect, request
import werkzeug

from . import models, tasks

blueprint = Blueprint("extract", __name__, url_prefix='/extracts')


class ValidationError(werkzeug.exceptions.BadRequest):
    """Error in validating user-provided data."""
    code = 400
    description = 'Invalid data provided.'


def validate_tweet_ids(tweet_ids: typing.Iterable[str]) -> typing.List[int]:
    """Cast Tweet IDs to integer or raise ValidationError."""
    if not tweet_ids:
        raise ValidationError('No Tweet IDs were found.')

    try:
        return [int(tweet_id) for tweet_id in tweet_ids]

    except ValueError as exc:
        raise ValidationError('Tweet IDs must be integers.') from exc


@blueprint.route('/', methods=['POST'])
def request_extract():
    """View to request a Twitter Extract Bundle."""
    tweet_ids = request.form['tweet_ids'].splitlines()
    tweet_ids = validate_tweet_ids(tweet_ids)

    extract = models.Extract(email=request.form['email'])
    extract.save()

    tasks.build_extract.delay(extract.uuid, tweet_ids)

    return redirect(extract.get_absolute_url())


@blueprint.route('/<uuid:extract_uuid>')
def download_extract(extract_uuid):
    """View to download a Twitter Extract Bundle."""
    extract = models.Extract.query.get(str(extract_uuid))

    return render_template('extract.html', extract=extract)
