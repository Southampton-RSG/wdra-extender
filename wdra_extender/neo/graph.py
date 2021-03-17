"""Module containing neo4j database connection and construction tools"""

from flask import Flask, g, Response, request
from neo4j import GraphDatabase, basic_auth

from ..extract.tools import ContextProxyLogger
# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)