"""Module containing setup code for Flask extensions."""
import typing

from celery import Celery
import flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

__all__ = [
    'celery',
    'db',
    'migrate',
    'login_manager',
]


class FlaskCelery(Celery):
    """Celery wrapper to support binding of the Flask context.

    See https://stackoverflow.com/a/14146403 for reference.
    """
    def __init__(self, *args, **kwargs):
        super(FlaskCelery, self).__init__(*args, **kwargs)
        self.patch_task()

        if 'app' in kwargs:
            self.init_app(kwargs['app'])

        # Need to discover tasks here so the worker can see them too
        self.autodiscover_tasks(['wdra_extender.extract'])

    def patch_task(self):
        """Give Celery Task type access to the Flask context."""
        TaskBase = self.Task
        _celery = self

        class ContextTask(TaskBase):  # pylint: disable=too-few-public-methods
            """Celery Task class with access to the Flask context."""
            abstract = True

            def __call__(self, *args, **kwargs):
                if flask.has_app_context():
                    return TaskBase.__call__(self, *args, **kwargs)

                with _celery.app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)

        self.Task = ContextTask  # pylint: disable=invalid-name

    def init_app(self, app):
        """Initialize Celery configuration from the Flask app config dictionary."""
        def get_celery_keys(config: typing.Mapping) -> typing.Dict:
            return {
                k.replace('CELERY_', '', 1): v
                for k, v in config.items() if k.startswith('CELERY_')
            }

        self.app = app
        self.config_from_object(get_celery_keys(app.config))


celery = FlaskCelery()  # pylint: disable=invalid-name
db = SQLAlchemy()  # pylint: disable=invalid-name
migrate = Migrate()  # pylint: disable=invalid-name
login_manager = LoginManager()  # pylint: disable=invalid-name
