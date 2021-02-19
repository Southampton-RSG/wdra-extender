from flask_login import UserMixin
from ..extensions import db

from ..extract.tools import ContextProxyLogger
# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)

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
    bearer_token = db.Column(db.String(), nullable=True)
    consumer_key = db.Column(db.String(), nullable=True)
    consumer_secret = db.Column(db.String(), nullable=True)
    access_token = db.Column(db.String(), nullable=True)
    access_token_secret = db.Column(db.String(), nullable=True)

    def set_keys(self, form):
        self.bearer_token = form.get('bearer_token')
        self.consumer_key = form.get('consumer_key')
        self.consumer_secret = form.get('consumer_secret')
        self.access_token = form.get('access_token')
        self.access_token_secret = form.get('access_token_secret')
        self.twitter_keys_set = True
        self.save()

    def get_key(self, key: str):
        return self.__getattribute__(key)

    def twitter_key_dict(self):
        twitter_keys = {endpoint_name:
                        {
                            'bearer_token': self.bearer_token,
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
