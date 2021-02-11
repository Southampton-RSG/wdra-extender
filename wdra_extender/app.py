"""Module containing the Flask App itself.

This is the entrypoint to WDRA-Extender.
"""

# pylint: disable=redefined-outer-name

import importlib

from flask import Flask, render_template, request

from wdra_extender import extract
from wdra_extender.extensions import celery, db, migrate

__all__ = [
    'app',
    'celery',
]


def create_app(config_module='wdra_extender.settings'):
    """App factory as in https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/.

    :param config_object: Configuration object to use.
    """
    config = importlib.import_module(config_module)

    app = Flask(__name__)
    app.config.from_object(config)
    app.logger.setLevel(config.LOG_LEVEL)

    app.logger.debug('Logger initialised')

    register_extensions(app)
    register_blueprints(app)

    return app


def register_extensions(app) -> None:
    """Initialise all Flask extensions.

    This populates settings and gives them access to the Flask context.

    :param app: Flask App which extensions should be initialised to.
    """
    if app.config['CELERY_BROKER_URL']:
        celery.init_app(app)

    else:
        app.logger.warning(
            'Running without task queue - not suitable for production')

    db.init_app(app)
    migrate.init_app(app, db)


def register_blueprints(app) -> None:
    """Register all views with the Flask controller.

    :param app: Flask App which views should be registered to.
    """
    app.register_blueprint(extract.views.blueprint)


app = create_app()  # pylint: disable=invalid-name


@app.before_request
def log_request():
    """Log each request received."""
    app.logger.debug(repr(request))


@app.route('/')
def index():
    """Static page where users will land when first accessing WDRA-Extender."""
    return render_template('index.html')
