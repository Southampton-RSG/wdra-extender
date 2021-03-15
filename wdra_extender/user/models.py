from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from ..extensions import db, login_manager
from ..extract.tools import ContextProxyLogger
# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)

__all__ = [
    'WdraxUser',
]


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return WdraxUser.query.get(int(user_id), None)


class WdraxUser(UserMixin, db.Model):
    """A Twitter Extract Bundle.

    A user of the website with associated extracts and auth keys
    """

    # pylint: disable=no-member
    __tablename__ = 'wdrax_users'

    id = db.Column(db.Integer, unique=True, primary_key=True)  # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(1000), unique=True)
    password = db.Column(db.String(100))
    extracts = db.relationship('Extract')

    # these keys may need to be adjusted if in the future different keys are required for different endpoints
    twitter_keys_set = db.Column(db.Boolean, default=False)
    bearer_token = db.Column(db.String(), nullable=True)
    consumer_key = db.Column(db.String(), nullable=True)
    consumer_secret = db.Column(db.String(), nullable=True)
    access_token = db.Column(db.String(), nullable=True)
    access_token_secret = db.Column(db.String(), nullable=True)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

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
                            'access_token': self.access_token,
                            'access_token_secret': self.access_token_secret,
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
