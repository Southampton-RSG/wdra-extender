from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from celery import Celery

from . import settings

__all__ = [
    'celery',
    'db',
    'migrate',
]

celery = Celery('wdra', broker=settings.CELERY_BROKER_URL)
db = SQLAlchemy()
migrate = Migrate()
