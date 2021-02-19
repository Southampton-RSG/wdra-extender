"""Module containing the Flask App itself.

This is the entrypoint to WDRA-Extender.
"""

# pylint: disable=redefined-outer-name

import importlib

from flask import Flask, render_template, request

from wdra_extender import user
from wdra_extender import extract
from wdra_extender.extensions import make_celery, db, migrate, login_manager

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

    _celery = register_extensions(_app)
    register_blueprints(_app)

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return user.models.User.query.get(int(user_id))
    return _app, _celery


def register_extensions(_app):
    """Initialise all Flask extensions.

    This populates settings and gives them access to the Flask context.

    :param _app: Flask App which extensions should be initialised to.
    """
    if _app.config['CELERY_BROKER_URL']:
        _celery = make_celery(_app)

    else:
        _app.logger.warning(
            'Running without task queue - not suitable for production')

    db.init_app(_app)
    migrate.init_app(_app, db)
    login_manager.init_app(_app)
    return _celery


def register_blueprints(_app) -> None:
    """Register all views with the Flask controller.

    :param _app: Flask App which views should be registered to.
    """
    _app.register_blueprint(extract.views.blueprint_extract)
    _app.register_blueprint(user.auth.blueprint_auth)


app, celery = create_app()  # pylint: disable=invalid-name


@app.before_request
def log_request():
    """Log each request received."""
    app.logger.debug(repr(request))


@app.route('/')
def index():
    """Static page where users will land when first accessing WDRA-Extender."""
    return render_template('index.html')
