"""Module containing neo4j database connection and construction tools"""

from flask import current_app, g, session
from flask_login import login_required, current_user
from neo4j import GraphDatabase, basic_auth

from ..app import neo_db
from ..extract.tools import ContextProxyLogger
# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)


__all__ = [
    'get_db',
    'serialize_movie',
    'serialize_cast'
]

# bring the contextualised database object into the local scope to be used by the neo_view and local functions
get_db = neo_db.get_db


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
