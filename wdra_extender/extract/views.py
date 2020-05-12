from flask import Blueprint, render_template, redirect, request, url_for

from . import models

blueprint = Blueprint("extract", __name__, url_prefix='/extracts')


@blueprint.route('/', methods=['POST'])
def request_extract():
    """View to request a Twitter Extract Bundle."""
    extract = models.Extract(email=request.form['email'])
    extract.save()

    return redirect(extract.get_absolute_url())


@blueprint.route('/<uuid:extract_uuid>')
def download_extract(extract_uuid):
    """View to download a Twitter Extract Bundle."""
    extract = models.Extract.query.get(str(extract_uuid))

    return render_template('extract.html', extract=extract)
