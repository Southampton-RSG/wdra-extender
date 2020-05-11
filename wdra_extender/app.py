import logging
import sys

from flask import Flask, render_template, request

from . import extract


def create_app():
    """App factory as in https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../db.sqlite3'

    register_extensions(app)
    register_blueprints(app)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app


def register_extensions(app) -> None:
    from .extensions import (
        db,
        migrate,
    )
    db.init_app(app)
    migrate.init_app(app, db)


def register_blueprints(app) -> None:
    app.register_blueprint(extract.views.blueprint)


def configure_logger(app) -> None:
    handler = logging.StreamHandler(sys.stdout)

    if not app.logger.handlers:
        app.logger.addHandler(handler)
