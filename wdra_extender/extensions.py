"""Module containing setup code for Flask extensions."""
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from celery import Celery

__all__ = [
    'db',
    'migrate',
    'login_manager',
    'make_celery'
]


db = SQLAlchemy()  # pylint: disable=invalid-name
migrate = Migrate()  # pylint: disable=invalid-name
login_manager = LoginManager()  # pylint: disable=invalid-name


def make_celery(_app):
    celery = Celery(
        __name__,
        backend=f'redis://localhost:6379/0',
        broker=f'redis://localhost:6379/0'
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
