"""Module containing Celery tasks related to Twitter Extract Bundles."""
from .app import celery
from .extract.models import Extract
from .user.models import User


@celery.task
def build_extract(uuid, query, **kwargs):
    """Begin the build of a requested Twitter Extract Bundle."""
    extract = Extract.query.get(uuid)
    user = User.query.get(extract.user_id)
    twitter_key_dict = user.twitter_key_dict()
    extract.building = True
    extract.save()
    return extract.build(query, twitter_key_dict,  **kwargs)


@celery.task
def rebuild_extract(uuid):
    """Begin the rebuild of a requested Twitter Extract Bundle."""
    extract = Extract.query.get(uuid)
    user = User.query.get(extract.user_id)
    twitter_key_dict = user.twitter_key_dict()
    extract.building = True
    extract.save()
    return extract.rebuild(twitter_key_dict)
