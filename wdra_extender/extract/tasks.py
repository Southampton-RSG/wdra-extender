
from ..extensions import celery


@celery.task()
def build_extract(extract_dict):
    """Begin the build of a requested Twitter extract."""
    from .models import Extract

    extract = Extract(**extract_dict)
    return extract.build()
