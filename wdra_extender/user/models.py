from flask import current_app, url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db, login_manager

__all__ = [
    'User',
]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(1000))

    twitter_keys = {
        'consumer_key': db.Column(db.String(), nullable=True),
        'consumer_secret': db.Column(db.String(), nullable=True),
        'access_token': db.Column(db.String(), nullable=True),
        'access_secret': db.Column(db.String(), nullable=True),
        'barer_token': db.Column(db.String(), nullable=True),
    }

    def save(self) -> None:
        """Save this model to the database."""
        self.make_id()
        db.session.add(self)
        db.session.commit()
