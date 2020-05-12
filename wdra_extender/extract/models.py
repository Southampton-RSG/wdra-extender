"""This module contains the Extract model and supporting functionality."""

import time
import uuid

from flask import url_for

from . import tasks
from ..extensions import db

__all__ = [
    'Extract',
]


class Extract(db.Model):
    """A Twitter Extract Bundle."""

    #: UUID identifier for the Bundle - acts as PK
    uuid = db.Column(db.String(36),
                     default=lambda: str(uuid.uuid4()),
                     index=True,
                     nullable=False,
                     primary_key=True,
                     unique=True)

    #: Email address of person who requested thd Bundle
    email = db.Column(db.String(254), index=True, nullable=False)

    #: Is the Bundle ready for pickup?
    ready = db.Column(db.Boolean, default=False, index=True, nullable=False)

    def save(self) -> None:
        db.session.add(self)
        db.session.commit()

    def submit_task(self):
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
        return url_for('extract.download_extract', extract_uuid=self.uuid)
