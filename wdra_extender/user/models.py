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
    password = db.Column(db.String(100))

    # these keys may need to be adjusted if in the future different keys are required for different endpoints
    twitter_keys_set = db.Column(db.Boolean, default=False)
    barer_token = db.Column(db.String(), nullable=True)
    consumer_key = db.Column(db.String(), nullable=True)
    consumer_secret = db.Column(db.String(), nullable=True)
    access_token = db.Column(db.String(), nullable=True)
    access_token_secret = db.Column(db.String(), nullable=True)

    def twitter_key_dict(self):
        twitter_keys = {endpoint_name:
                        {
                            'barer_token': self.barer_token,
                            'consumer_key': self.consumer_key,
                            'consumer_secret': self.consumer_secret,
                            'endpoint': f'https://api.twitter.com/2/{endpoint_str}'
                        }
                        for endpoint_name, endpoint_str in [['get_tweets_by_id', 'tweets/'],
                                                            ['search_tweets', 'tweets/search/recent'],
                                                            ['user_mention', 'users/:id/mentions'],
                                                            ['user_tweets', 'users/:id/tweet']
                                                            ]
                        }
        return twitter_keys

    def save(self) -> None:
        """Save this model to the database."""
        db.session.add(self)
        db.session.commit()
