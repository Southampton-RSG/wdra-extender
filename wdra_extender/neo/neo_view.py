"""Module containing views to support display and interaction with neo4j"""
from flask import Blueprint, current_app, g, render_template, redirect, request, Response, url_for, session, send_from_directory
from flask_login import login_required, current_user

from json import dumps

from . import graph
from ..extract.models import Extract
from ..tools import ContextProxyLogger
from ..extensions import neo_db

# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)

blueprint_neo = Blueprint("neo", __name__, url_prefix='/wdrax/neo')


@blueprint_neo.route("/display")
def show_graph():
    return send_from_directory(filename='neo_graph.html',
                               directory=current_app.config['BASE_DIR'].joinpath('wdra_extender/templates'))


@blueprint_neo.route("/graph")
def get_graph():
    db = neo_db.get_db()
    results = db.read_transaction(lambda tx: list(tx.run("MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) "
                                                         "RETURN m.title as movie, collect(a.name) as cast "
                                                         "LIMIT $limit", {
                                                             "limit": request.args.get("limit",
                                                                                       100)})))
    nodes = []
    rels = []
    i = 0
    for record in results:
        nodes.append({"title": record["movie"], "label": "movie"})
        target = i
        i += 1
        for name in record['cast']:
            actor = {"title": name, "label": "actor"}
            try:
                source = nodes.index(actor)
            except ValueError:
                nodes.append(actor)
                source = i
                i += 1
            rels.append({"source": source, "target": target})
    return Response(dumps({"nodes": nodes, "links": rels}),
                    mimetype="application/json")


@blueprint_neo.route("/search")
def get_search():
    try:
        q = request.args["q"]
    except KeyError:
        return []
    else:
        db = neo_db.get_db()
        results = db.read_transaction(lambda tx: list(tx.run("MATCH (movie:Movie) "
                                                             "WHERE movie.title =~ $title "
                                                             "RETURN movie", {"title": "(?i).*" + q + ".*"}
                                                             )))
        return Response(dumps([graph.serialize_movie(record['movie']) for record in results]),
                        mimetype="application/json")


@blueprint_neo.route("/movie/<title>")
def get_movie(title):
    db = neo_db.get_db()
    result = db.read_transaction(lambda tx: tx.run("MATCH (movie:Movie {title:$title}) "
                                                   "OPTIONAL MATCH (movie)<-[r]-(person:Person) "
                                                   "RETURN movie.title as title,"
                                                   "COLLECT([person.name, "
                                                   "HEAD(SPLIT(TOLOWER(TYPE(r)), '_')), r.roles]) AS cast "
                                                   "LIMIT 1", {"title": title}).single())

    return Response(dumps({"title": result['title'],
                           "cast": [graph.serialize_cast(member)
                                    for member in result['cast']]}),
                    mimetype="application/json")


@blueprint_neo.route("/upload_extract/<extract_uuid>")
def upload_extract(extract_uuid):
    db = neo_db.get_db()
    extract = Extract.get(extract_uuid)
    graph.process_extracts()
