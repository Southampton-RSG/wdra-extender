"""Module containing Celery tasks related to Twitter Extract Bundles."""

from ..extensions import celery
from .models import Extract


@celery.task()
def build_extract(uuid, tweet_ids):
    """Begin the build of a requested Twitter Extract Bundle."""
    extract = Extract.query.get(uuid)
    return extract.build(tweet_ids)
