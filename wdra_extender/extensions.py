"""Module containing setup code for Flask extensions."""
from celery import Celery
from flask import g
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
    'neo_db'
]


db = SQLAlchemy()  # pylint: disable=invalid-name
migrate = Migrate()  # pylint: disable=invalid-name

login_manager = LoginManager()  # pylint: disable=invalid-name
session = Session()  # pylint: disable=invalid-name


class MakeNeo:

    def __init__(self):
        self.current_app = None
        self.driver = None

    def init_app(self, _app):
        self.current_app = _app
        self.driver = GraphDatabase.driver(_app.config['NEO4J_URI'],
                                           auth=basic_auth(_app.config['NEO4J_USER'],
                                                           _app.config['NEO4J_PASSWORD']
                                                           )
                                           )

    def get_db(self):
        """
        Function to return the neo4j database driver associated with the application else
        create, assign, and return a driver for the neo4j session.
        """
        if not hasattr(g, 'neo4j_db'):
            if self.current_app.config['NEO4J_VERSION'].startswith("4"):
                g.neo4j_db = self.driver.session(database=self.current_app.config['NEO4J_DATABASE'])
            else:
                g.neo4j_db = self.driver.session()
        return g.neo4j_db


neo_db = MakeNeo()


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
