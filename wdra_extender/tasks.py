"""Module containing Celery tasks related to Twitter Extract Bundles."""
from .app import celery
from .extract.models import Extract
from .user.models import WdraxUser

__all__ = [
    'build_extract',
    'rebuild_extract'
]


@celery.task(bind=True)
def build_extract(self, uuid, query, **kwargs):
    """Begin the build of a requested Twitter Extract Bundle."""
    extract = Extract.query.get(uuid)
    user = WdraxUser.query.get(extract.user_id)
    twitter_key_dict = user.twitter_key_dict()
    extract.building = True
    extract.save()
    state_function = self.update_state
    return extract.build(query, twitter_key_dict, state_function, **kwargs)


@celery.task
def rebuild_extract(uuid):
    """Begin the rebuild of a requested Twitter Extract Bundle."""
    extract = Extract.query.get(uuid)
    user = WdraxUser.query.get(extract.user_id)
    twitter_key_dict = user.twitter_key_dict()
    extract.building = True
    extract.save()
    return extract.rebuild(twitter_key_dict)
