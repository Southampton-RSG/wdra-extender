
from ..extensions import celery


@celery.task()
def build_extract(uuid):
    """Begin the build of a requested Twitter extract."""
    from .models import Extract

    extract = Extract.query.get(uuid)
    return extract.build()
