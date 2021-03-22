"""Module containing neo4j database connection and construction tools"""

from flask import current_app, g, session
from flask_login import login_required, current_user
from neo4j import GraphDatabase, basic_auth

from ..extensions import neo_db
from ..tools import ContextProxyLogger
# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)


__all__ = [
    'serialize_movie',
    'serialize_cast',
    'process_extracts'
]


# Process Extracts to return uploadable schemas ========================================================================
def process_extracts(extract):
    # psudocode
    # load json objects
    # parse the jason object into individual tweets each to be a node.
    # # try to identify corporations/governments to tag differently
    # # try to identify sentiment of each tweet
    # # get lists of '#' to create node relations
    # # get lists of '@' to create node relations
    # parse the search
    # # create search term nodes (check existing @ and or #)
    # # embed a includes or excludes to each tweet in the extract
    #
    # Build the query to do the insertion

    pass
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
