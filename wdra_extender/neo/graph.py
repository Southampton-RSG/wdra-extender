"""Module containing neo4j database connection and construction tools"""

from flask import current_app, g, session
from flask_login import login_required, current_user
from neo4j import GraphDatabase, basic_auth

from ..extensions import driver
from ..extract.tools import ContextProxyLogger
# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)


__all__ = [
    'get_db',
    'serialize_movie',
    'serialize_cast'
]


# These functions handle the database in the application context =======================================================
def get_db():
    """
    Function to return the neo4j database driver associated with the application else
    create, assign, and return a driver for the neo4j session.
    """
    if not hasattr(g, 'neo4j_db'):
        if current_app.config['NEO4J_VERSION'].startswith("4"):
            g.neo4j_db = driver.session(database=current_app.config['NEO4J_DATABASE'])
        else:
            g.neo4j_db = driver.session()
    return g.neo4j_db


@current_app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'neo4j_db'):
        g.neo4j_db.close()
# ======================================================================================================================


# These functions are database management and extention tools. They can/will oad tweets request new tweets and more ====
# TODO: These are placeholders from the example https://github.com/neo4j-examples/movies-python-bolt/blob/main/movies.py
def serialize_movie(movie):
    return {
        'id': movie['id'],
        'title': movie['title'],
        'summary': movie['summary'],
        'released': movie['released'],
        'duration': movie['duration'],
        'rated': movie['rated'],
        'tagline': movie['tagline']
    }


def serialize_cast(cast):
    return {
        'name': cast[0],
        'job': cast[1],
        'role': cast[2]
    }
# ======================================================================================================================
