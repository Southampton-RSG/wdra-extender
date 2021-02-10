"""Module containing views related to Twitter Extract Bundles."""
import pathlib

from flask import Blueprint, current_app, render_template, redirect, request, send_from_directory, url_for, session

from . import models, tasks, tools


blueprint_extract = Blueprint("extract", __name__, url_prefix='/extract')


def get_from_session():
    rich_dict = {}
    if 'extract' in session.keys():
        rich_dict['extract'] = models.Extract.query.get(session['extract'])
    if 'user' in session.keys():
        rich_dict['user'] = models.load_user(user_id=session['user'])
    return rich_dict


@blueprint_extract.route('/', methods=['POST', 'GET'])
def check_email():
    """View to get the user email and create a uuid"""
    if request.method == 'GET':
        return render_template('index.html')
    if request.method == 'POST':
        user_email = request.form['email']
        user = models.load_user(user_email=user_email)
        if user is not None:
            # authenticate user here
            session['user'] = user.id
            return redirect(url_for('extract.login'))
        elif user is None:
            session['new_user_email'] = user_email
            return redirect(url_for('extract.new_user'))


@blueprint_extract.route('/login/', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('index.html', user_email=session['user'].user_email, auth_fail=False)
    elif request.method == 'POST':
        #Auth user here
        if False:
            return redirect(url_for('extract.method_select'))
        else:
            return render_template('login.html', user_email=session['user'].user_email, auth_fail=True)


@blueprint_extract.route('/new_user/', methods=['POST', 'GET'])
def new_user():
    rich_session = get_from_session()
    if request.method == 'GET':
        email = session['new_user_email']
        return render_template('new_user.html', user_email=session['new_user_email'])
    elif request.method == 'POST':
        for attribute in rich_session['user'].__dict__.keys():
            if attribute in request.form:
                rich_session['user'][attribute] = request.form[attribute]
        rich_session['user'].save()
        return redirect(url_for('extract.method_select'))


# Methods for selecting search parameters ==============================================================================
@blueprint_extract.route('/method/', methods=['GET', 'POST'])
def select_method():
    """View to select the extract method"""
    extract_methods = {
        'Search': 'extract.get_by_search',
        'ID': 'extract.get_by_id',
        'Replication': 'extract.get_by_replication'
    }
    rich_session = get_from_session()
    if request.method == "POST":
        selected = request.form.get('method_select')
        # Create a new extract to handle the users next request
        rich_session['extract'] = models.Extract(user_id=session['user'].get_id())
        session['extract'] = rich_session['extract'].uuid
        rich_session['extract'].extract_method = selected
        rich_session['extract'].save()
        return redirect(url_for(extract_methods[selected], basic_form=True, extract_uuid=rich_session['extract']['uuid']))
    else:
        return render_template('get_method.html')
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
        if ('submit_basic' in request.form) or ('submit_adv' in request.form):
            inc_terms = str(request.form['include_terms']).split(sep=',')
            exc_terms = str(request.form['exclude_terms']).split(sep=',')
            query = ""
            query += " ".join(inc_terms)
            if len(exc_terms) > 0:
                query += " -" + " -".join(exc_terms)
            query += ''
            # get the additional constraints and return fields
            adv_dict = {'results_per_call': 10,
                        'max_results': 10,
                        'tweet_fields': ["id", "text"],
                        'user_fields': [],
                        'media_fields': [],
                        'place_fields': [],
                        'poll_fields': [],
                        'expansions': []}
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
            for key in ['tweet_fields', 'user_fields', 'media_fields',
                        'place_fields', 'poll_fields', 'expansions']:
                if len(adv_dict[key]) == 0:
                    adv_dict[key] = None
                else:
                    adv_dict[key] = ",".join(adv_dict[key])

            extract = models.Extract.query.get(str(extract_uuid))
            if current_app.config['CELERY_BROKER_URL']:
                # Add job to task queue
                tasks.build_extract.delay(extract.uuid, query, **adv_dict)

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
