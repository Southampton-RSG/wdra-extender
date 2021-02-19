"""Module containing Celery tasks related to Twitter Extract Bundles."""

from .models import Extract
from flask import current_app
from flask_login import login_required


@login_required
def build_extract(uuid, query, **kwargs):
    """Begin the build of a requested Twitter Extract Bundle."""
    extract = Extract.query.get(uuid)
    return extract.build(query, **kwargs)
