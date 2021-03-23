"""Module containing the Flask App itself.

This is the entrypoint to WDRA-Extender.
"""

# pylint: disable=redefined-outer-name

import importlib

from flask import Flask, request, g

from wdra_extender import main, user, extract, neo
from wdra_extender.extensions import db, login_manager, make_celery, neo_db, migrate, session

__all__ = [
    'app',
    'celery',
    'create_app'
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

    # neo4j
    neo_db.init_app(_app)

    # account manager
    login_manager.init_app(_app)
    login_manager.login_view = "auth.login"

    # server side session
    session.init_app(_app)

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
    _app.register_blueprint(neo.neo_view.blueprint_neo)


app, celery = create_app()  # pylint: disable=invalid-name


@app.before_request
def log_request():
    """Log each request received."""
    app.logger.debug(repr(request))


@app.teardown_appcontext
def close_db(error):
    """Close the DB in event of app shutdown"""
    if hasattr(g, 'neo4j_db'):
        g.neo4j_db.close()
