"""Module containing the Extract model and supporting functionality."""

import time
from uuid import uuid4

from flask import url_for

from . import tasks
from ..extensions import db

__all__ = [
    'Extract',
]


class Extract(db.Model):
    """A Twitter Extract Bundle.

    A Twitter Extract Bundle is a collection of files produced by the Twitter
    data analysis scripts from a list of Tweet ids.
    """
    # pylint: disable=no-member

    #: UUID identifier for the Bundle - acts as PK
    uuid = db.Column(db.String(36),
                     default=lambda: str(uuid4()),
                     index=True,
                     nullable=False,
                     primary_key=True,
                     unique=True)

    #: Email address of person who requested the Bundle
    email = db.Column(db.String(254), index=True, nullable=False)

    #: Is the Bundle ready for pickup?
    ready = db.Column(db.Boolean, default=False, index=True, nullable=False)

    def save(self) -> None:
        """Save this model to the database."""
        db.session.add(self)
        db.session.commit()

    def queue_build(self):
        """Trigger the building of this extract bundle."""
        tasks.build_extract.delay(self.uuid)

    def build(self):
        """Build a requested Twitter extract.

        Called by `extract.tasks.build_extract` Celery task.
        """
        time.sleep(10)
        print(self.uuid)

        self.ready = True
        self.save()
        return self.uuid

    def get_absolute_url(self):
        """Get the URL for this object's detail view."""
        return url_for('extract.download_extract', extract_uuid=self.uuid)
