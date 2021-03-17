"""Module containing setup code for Flask extensions."""
from celery import Celery
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from neo4j import GraphDatabase, basic_auth

__all__ = [
    'db',
    'login_manager',
    'make_celery',
    'migrate',
    'session',
    'driver',
    'drive_neo'
]


db = SQLAlchemy()  # pylint: disable=invalid-name
migrate = Migrate()  # pylint: disable=invalid-name

login_manager = LoginManager()  # pylint: disable=invalid-name
session = Session()  # pylint: disable=invalid-name

driver = None


def drive_neo(_app):
    global driver
    driver = GraphDatabase.driver(_app.config['NEO4J_URI'],
                                  auth=basic_auth(_app.config['NEO4J_USER'],
                                                  _app.config['NEO4J_PASSWORD']
                                                  )
                                  )


def make_celery(_app):
    """celery = Celery(
        __name__,
        backend=f'redis://redis:6379/0',
        broker=f'redis://redis:6379/0'
    )"""
    celery = Celery(
        __name__,
        backend=_app.config['CELERY_BROKER_URL'],
        broker=_app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(_app.config)
    TaskBase = celery.Task  # pylint: disable=invalid-name

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with _app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    return celery
