from flask import Blueprint, render_template, request

from . import models

blueprint = Blueprint("extract", __name__, url_prefix='/extracts')


@blueprint.route('/', methods=['POST'])
def request_extract():
    """View to request a Twitter Extract Bundle."""
    extract = models.Extract(email=request.form['email'])
    extract.save()

    return extract.uuid


@blueprint.route('/<uuid:extract_id>')
def download_extract(extract_id):
    """View to download a Twitter Extract Bundle."""
    raise NotImplementedError
