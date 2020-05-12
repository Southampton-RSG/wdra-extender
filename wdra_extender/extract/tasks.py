
from ..extensions import celery


@celery.task()
def build_extract(extract_dict):
    """Build a requested Twitter extract."""
    from .models import Extract

    extract = Extract(**extract_dict)

    print(extract.uuid)
    return extract.uuid
