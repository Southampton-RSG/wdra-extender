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
# Need to discover tasks here so the worker can see them too
celery.autodiscover_tasks(['wdra_extender.extract'], force=True)

db = SQLAlchemy()
migrate = Migrate()
