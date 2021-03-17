"""Module containing the Flask App itself.

This is the entrypoint to WDRA-Extender.
"""

# pylint: disable=redefined-outer-name

import importlib

from flask import Flask, request

from wdra_extender import main, user, extract
from wdra_extender.extensions import db, login_manager, make_celery, migrate, session

__all__ = [
    'app',
    'celery',
    'create_app',
]


def create_app(config_module='wdra_extender.settings'):
    """App factory as in https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/.

    :param config_module: Configuration object to use.
    """
    config = importlib.import_module(config_module)

    _app = Flask(__name__)
    _app.config.from_object(config)
    _app.logger.setLevel(config.LOG_LEVEL)

    _app.logger.debug('Logger initialised')

    register_blueprints(_app)
    _celery = register_extensions(_app)

    return _app, _celery


def register_extensions(_app):
    """Initialise all Flask extensions.

    This populates settings and gives them access to the Flask context.

    :param _app: Flask App which extensions should be initialised to.
    """

    # database and migrations
    db.init_app(_app)
    migrate.init_app(_app, db)

    # account manager
    login_manager.init_app(_app)
    login_manager.login_view = "auth.login"

    # server side session
    #session.init_app(_app)

    # job runner
    _celery = make_celery(_app)

    return _celery


def register_blueprints(_app) -> None:
    """Register all views with the Flask controller.

    :param _app: Flask App which views should be registered to.
    """
    _app.register_blueprint(main.routes.blueprint_index)
    _app.register_blueprint(extract.views.blueprint_extract)
    _app.register_blueprint(user.auth.blueprint_auth)


app, celery = create_app()  # pylint: disable=invalid-name


@app.before_request
def log_request():
    """Log each request received."""
    app.logger.debug(repr(request))
