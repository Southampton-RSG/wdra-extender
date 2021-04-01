"""Module containing views related to Twitter Extract Bundles."""
import pathlib
from time import time
from datetime import datetime

from flask import Blueprint, current_app, render_template, redirect, request, send_from_directory, url_for, session
from flask_login import login_required, current_user
from . import models
from . import extract_tools
from ..tools import ContextProxyLogger, kill_task

blueprint_extract = Blueprint("extract", __name__, url_prefix='/wdrax/extract')

# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)


def get_from_session():
    rich_dict = {}
    if 'extract' in session.keys():
        rich_dict['extract'] = models.Extract.query.get(session['extract'])
    if 'user' in session.keys():
        rich_dict['user'] = models.load_user(user_id=session['user'])
    return rich_dict


# Methods for selecting search parameters ==============================================================================
@blueprint_extract.route('/method/', methods=['GET', 'POST'])
def select_method():
    """View to select the extract method"""
    extract_methods = {
        'Search': 'extract.get_by_search',
        'ID': 'extract.get_by_id',
        # 'Replication': 'extract.get_by_replication'
    }
    rich_session = get_from_session()
    if request.method == "POST":
        selected = request.form.get('method_select')
        return redirect(url_for(extract_methods[selected], basic_form=True))
    else:
        return render_template('get_method.html', extract_methods=extract_methods)
# ======================================================================================================================


# Methods for getting the twitter data =================================================================================
@blueprint_extract.route('/method/search/<basic_form>/', methods=['GET', 'POST'])
@login_required
def get_by_search(basic_form):
    """View to request a Twitter extract Bundle using search parameters"""
    if request.method == 'GET':
        return render_template('get_by_search.html',
                               basic_form=basic_form,
                               return_fields=current_app.config['TWITTER_RETURN_DICT'],
                               endpoints=current_user.endpoints)
    if request.method == 'POST':
        if 'switch_form' in request.form:
            if basic_form == "True":
                basic_form = "False"
            else:
                basic_form = "True"
            return render_template('get_by_search.html',
                                   basic_form=basic_form,
                                   return_fields=current_app.config['TWITTER_RETURN_DICT'],
                                   endpoints=current_user.endpoints)
        if ('submit_basic' in request.form) or ('submit_adv' in request.form):
            # Parse the text input fields and create a valid search
            # The include terms get separated on commas
            inc_terms = [term.strip() for term in str(request.form['include_terms']).split(sep=',')]
            logger.info(f"include list {inc_terms}")
            # Strip erroneous empty terms that may appear
            while '' in inc_terms:
                inc_terms.remove('')
            # The exclude terms get separated on commas
            exc_terms = [term.strip() for term in str(request.form['exclude_terms']).split(sep=',')]
            logger.info(f"exclude list {exc_terms}")
            # Strip erroneous empty terms that may appear
            while '' in exc_terms:
                exc_terms.remove('')
            # Assign a blank string to the query to build out on
            query = ""
            # Check that there are search terms then join to the search string
            assert len(inc_terms) > 0, "You must include at least one term to search for"
            query += " ".join(inc_terms)
            if len(exc_terms) > 0:
                query += " -" + " -".join(exc_terms)
            # get the additional constraints and return fields
            adv_dict = {'results_per_call': 10,
                        'tweet_fields': ["id", "text"],
                        'user_fields': [],
                        'media_fields': [],
                        'place_fields': [],
                        'poll_fields': [],
                        'expansions': [],
                        'max_results': 10,
                        'endpoint': request.form.get('endpoint', 'search_tweets')}
            if 'max_results' in request.form:
                adv_dict['max_results'] = request.form['max_results']
            if 'results_per_call' in request.form:
                adv_dict['results_per_call'] = request.form['results_per_call']
            if 'submit_adv' in request.form:
                for field in request.form.keys():
                    if field in ['start_time', 'end_time', 'stringify']:
                        adv_dict[field] = request.form[field]
                    if field == 'since_id':
                        if request.form[field] != '':
                            if request.form['from_inclusive']:
                                adv_dict[field] = request.form[field] - 1
                            else:
                                adv_dict[field] = request.form[field]
                    if field == 'until_id':
                        if request.form[field] != '':
                            if request.form['to_inclusive']:
                                adv_dict[field] = request.form[field] + 1
                            else:
                                adv_dict[field] = request.form[field]
                    # Basic return fields
                    if field in current_app.config['TWITTER_RETURN_DICT']['tweet_fields']:
                        if field not in ["poll_fields", "id", "text"]:
                            adv_dict['tweet_fields'] += [field]
                    # If checked then check for subfields
                    if 'author_id' in request.form.keys():
                        if field[1:] in current_app.config['TWITTER_RETURN_DICT']['author_id']:
                            adv_dict['user_fields'] += [field[1:]]
                    if 'attachments' in request.form.keys():
                        if field[1:] in current_app.config['TWITTER_RETURN_DICT']['attachments']:
                            adv_dict['media_fields'] += [field[1:]]
                    if 'geo' in request.form.keys():
                        if field[1:] in current_app.config['TWITTER_RETURN_DICT']['geo']:
                            adv_dict['place_fields'] += [field[1:]]
                    if 'poll_fields' in request.form.keys():
                        if field[1:] in current_app.config['TWITTER_RETURN_DICT']['poll_fields']:
                            adv_dict['poll_fields'] += [field[1:]]
                    if 'id' in request.form.keys():
                        if field[1:] in current_app.config['TWITTER_RETURN_DICT']['id']:
                            adv_dict['expansions'] += [field[1:]]
            # If no subfields are selected change the value to none
            for key in ['tweet_fields', 'user_fields', 'media_fields', 'place_fields', 'poll_fields', 'expansions']:
                if len(adv_dict[key]) == 0:
                    adv_dict[key] = None
                else:
                    adv_dict[key] = ",".join(adv_dict[key])

            # Create an extract model for the runner to work on
            extract = models.Extract(user_id=current_user.get_id())
            extract.extract_method = "Search"
            extract.save()

            # Add job to task queue
            current_app.logger.debug(f'Handing extract {extract.uuid} to queue\n'
                                     f'Query Str: {query}\n'
                                     f'Search Settings: {adv_dict}')

            from ..tasks import build_extract
            task = build_extract.apply_async(args=[extract.uuid, query], kwargs=adv_dict, task_id=extract.uuid)
            extract.queuing = True
            extract.save()
            current_app.logger.debug(f'Handed extract {extract.uuid} to queue')
            return redirect(url_for('extract.detail_extract', extract_uuid=extract.uuid))


@blueprint_extract.route('/method/id/', methods=['GET', 'POST'])
def get_by_id():
    """View to request a Twitter Extract Bundle using provided tweet IDs."""

    if request.method == "POST":
        tweet_ids = request.form['tweet_ids'].splitlines()
        tweet_ids = extract_tools.validate_tweet_ids(tweet_ids)

        # Create an extract model for the runner to work on
        extract = models.Extract(user_id=current_user.get_id())
        extract.extract_method = "ID"
        extract.save()

        # Add job to task queue
        current_app.logger.debug(f'Handing extract {extract.uuid} to queue')
        from ..tasks import build_extract
        task = build_extract.apply_async(args=[extract.uuid, tweet_ids], task_id=extract.uuid)
        extract.queuing = True
        extract.save()
        current_app.logger.debug(f'Handed extract {extract.uuid} to queue')
        return redirect(url_for('extract.detail_extract', extract_uuid=extract.uuid))
    else:
        return render_template('get_by_id.html')


@blueprint_extract.route('/method/replication/<uuid:extract_uuid>', methods=['POST'])
def get_by_replication(extract_uuid):
    """"""
    return None
# ======================================================================================================================


# Methods for managing the extract bundle once created==================================================================
@blueprint_extract.route('/show', methods=['GET', 'POST'])
@login_required
def show_extracts():
    """Display a list of the users previous Twitter Extract Bundles"""
    user_extracts = models.Extract.query.filter_by(user_id=int(current_user.id)).all()
    logger.debug(f"Extracts recieved:\n {user_extracts}")
    if request.method == 'GET':
        return render_template('all_extracts.html', user_extracts=user_extracts)


@blueprint_extract.route('/detail/<uuid:extract_uuid>')
def detail_extract(extract_uuid):
    """View displaying details of a Twitter Extract Bundle."""
    extract = models.Extract.query.get(str(extract_uuid))
    return render_template('extract.html', extract=extract, time_fun=time)


@blueprint_extract.route('/download/<uuid:extract_uuid>/fetch')
def download_extract(extract_uuid):
    """View to download a Twitter Extract Bundle."""
    return send_from_directory(current_app.config['OUTPUT_DIR'],
                               pathlib.Path(
                                    str(extract_uuid)).with_suffix('.zip'),
                               as_attachment=True)


@blueprint_extract.route('/delete_data/<uuid:extract_uuid>')
def delete_extract_data(extract_uuid):
    extract = models.Extract.query.get(str(extract_uuid))
    extract.delete_data()
    return redirect(url_for('extract.show_extracts'))


@blueprint_extract.route('/delete/<uuid:extract_uuid>')
def delete_extract(extract_uuid):
    extract = models.Extract.query.get(str(extract_uuid))
    extract.delete()
    return redirect(url_for('extract.show_extracts'))


@blueprint_extract.route('/rebuild/<uuid:extract_uuid>')
def rebuild_extract(extract_uuid):
    from ..tasks import rebuild_extract
    rebuild_extract.apply_async(args=[extract_uuid], task_id=extract_uuid)
    return redirect(url_for('extract.show_extracts'))

# ======================================================================================================================
