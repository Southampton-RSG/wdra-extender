import logging
import sys

from flask import Flask, render_template, request

from wdra_extender import extract

__all__ = [
    'create_app',
]


def create_app(config_object='wdra_extender.settings'):
    """App factory as in https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/.

    :param config_object: Configuration object to use.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app


def register_extensions(app) -> None:
    from .extensions import (
        celery,
        db,
        migrate,
    )

    db.init_app(app)
    migrate.init_app(app, db)

    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Celery Task class that can access the Flask context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask


def register_blueprints(app) -> None:
    app.register_blueprint(extract.views.blueprint)


def configure_logger(app) -> None:
    handler = logging.StreamHandler(sys.stdout)

    if not app.logger.handlers:
        app.logger.addHandler(handler)
