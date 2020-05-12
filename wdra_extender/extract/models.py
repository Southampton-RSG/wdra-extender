"""This module contains the Extract model and supporting functionality."""

import uuid

from . import tasks
from ..extensions import db


class Extract(db.Model):
    """A Twitter Extract Bundle."""
    uuid = db.Column(db.String(36),
                     default=lambda: str(uuid.uuid4()),
                     index=True,
                     nullable=False,
                     primary_key=True,
                     unique=True)

    email = db.Column(db.String(254), index=True, nullable=False)

    def save(self) -> None:
        db.session.add(self)
        db.session.commit()

        self.submit_task()

    def submit_task(self):
        extract_dict = {
            'uuid': self.uuid,
            'email': self.email,
        }
        tasks.build_extract.delay(extract_dict)
