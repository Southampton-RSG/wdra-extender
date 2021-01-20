"""Module containing views related to Twitter Extract Bundles."""
import pathlib

from flask import Blueprint, current_app, render_template, redirect, request, send_from_directory, url_for

from . import models, tasks, tools


blueprint_extract = Blueprint("extract", __name__, url_prefix='/extract')


# Methods for assigning a user ID and search parameters ================================================================
@blueprint_extract.route('/', methods=['POST'])
def extract_email():
    """View to get the user email and create a uuid"""
    extract = models.Extract(email=request.form['email'])
    extract.save()
    return redirect(url_for('extract.select_method', extract_uuid=extract.uuid))


@blueprint_extract.route('/method/<uuid:extract_uuid>', methods=['GET', 'POST'])
def select_method(extract_uuid):
    """View to select the extract method"""
    extract_methods = {
        'Search': 'extract.get_by_search',
        'ID': 'extract.get_by_id',
        'Replication': 'extract.get_by_replication'
    }

    if request.method == "POST":
        selected = request.form.get('method_select')
        extract = models.Extract.query.get(str(extract_uuid))
        extract.extract_method = selected
        extract.save()
        return redirect(url_for(extract_methods[selected], extract_uuid=extract_uuid, basic_form=True))
    else:
        return render_template('get_method.html', extract_methods=extract_methods, extract_uuid=extract_uuid)
# ======================================================================================================================


# Methods for getting the twitter data =================================================================================
@blueprint_extract.route('/method/search/<basic_form>/<uuid:extract_uuid>', methods=['GET', 'POST'])
def get_by_search(extract_uuid, basic_form):
    """View to request a Twitter extract Bundle using search parameters"""
    if request.method == 'GET':
        return render_template('get_by_search.html',
                               extract_uuid=extract_uuid,
                               basic_form=basic_form,
                               return_fields=current_app.config['TWITTER_RETURN_DICT'])
    if request.method == 'POST':
        if 'switch_form' in request.form:
            if basic_form == "True":
                basic_form = "False"
            else:
                basic_form = "True"
            return render_template('get_by_search.html',
                                   extract_uuid=extract_uuid,
                                   basic_form=basic_form,
                                   return_fields=current_app.config['TWITTER_RETURN_DICT'])
        if 'submit_basic' in request.form:
            inc_terms = str(request.form['search_terms']).split(sep=',')
            exc_terms = str(request.form['exclude_terms']).split(sep=',')
            query = ""
            query += " ".join(inc_terms)
            if len(exc_terms) > 0:
                query += " -" + " -".join(exc_terms)
        elif 'submit_adv' in request.form:
            pass
            # do more complicated stuff
        extract = models.Extract.query.get(str(extract_uuid))
        if current_app.config['CELERY_BROKER_URL']:
            # Add job to task queue
            tasks.build_extract.delay(extract.uuid, query)

        return redirect(extract.get_absolute_url())


@blueprint_extract.route('/method/id/<uuid:extract_uuid>', methods=['GET', 'POST'])
def get_by_id(extract_uuid):
    """View to request a Twitter Extract Bundle using provided tweet IDs."""

    if request.method == "POST":
        extract = models.Extract.query.get(str(extract_uuid))
        tweet_ids = request.form['tweet_ids'].splitlines()
        tweet_ids = tools.validate_tweet_ids(tweet_ids)

        if current_app.config['CELERY_BROKER_URL']:
            # Add job to task queue
            tasks.build_extract.delay(extract.uuid, tweet_ids)
        else:
            # Build the extract now
            extract.build(tweet_ids)

        return redirect(extract.get_absolute_url())
    else:
        return render_template('get_by_id.html', extract_uuid=extract_uuid)


@blueprint_extract.route('/method/replication/<uuid:extract_uuid>', methods=['POST'])
def get_by_replication(extract_uuid):
    """"""
    return None
# ======================================================================================================================


# Methods for managing the extract bundle once created==================================================================
@blueprint_extract.route('/detail/<uuid:extract_uuid>')
def detail_extract(extract_uuid):
    """View displaying details of a Twitter Extract Bundle."""
    extract = models.Extract.query.get(str(extract_uuid))

    return render_template('extract.html', extract=extract)


@blueprint_extract.route('/download/<uuid:extract_uuid>/fetch')
def download_extract(extract_uuid):
    """View to download a Twitter Extract Bundle."""
    return send_from_directory(current_app.config['OUTPUT_DIR'],
                               pathlib.Path(
                                   str(extract_uuid)).with_suffix('.zip'),
                               as_attachment=True)
# ======================================================================================================================
