"""Module containing setup code for Flask extensions."""

from celery import Celery
import flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

__all__ = [
    'celery',
    'db',
    'migrate',
]


class FlaskCelery(Celery):
    """Celery wrapper to support binding of the Flask context.

    See https://stackoverflow.com/a/14146403 for reference.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.patch_task()
        if 'app' in kwargs:
            self.init_app(kwargs['app'])

        # Need to discover tasks here so the worker can see them too
        self.autodiscover_tasks(['wdra_extender.extract'])

    def patch_task(self):
        TaskBase = self.Task
        _celery = self

        class ContextTask(TaskBase):  # pylint: disable=too-few-public-methods
            abstract = True

            def __call__(self, *args, **kwargs):
                if flask.has_app_context():
                    return TaskBase.__call__(self, *args, **kwargs)

                with _celery.app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)

        self.Task = ContextTask  # pylint: disable=invalid-name

    def init_app(self, app):
        self.app = app
        self.config_from_object(app.config)


celery = FlaskCelery()
db = SQLAlchemy()
migrate = Migrate()
