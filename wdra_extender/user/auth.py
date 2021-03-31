from flask import Blueprint, render_template, redirect, url_for, request, flash, session, send_from_directory, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse

from wdra_extender.extensions import db
from .models import WdraxUser
from ..tools import ContextProxyLogger
# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)

blueprint_auth = Blueprint('auth', __name__, url_prefix='/wdrax/auth')


# Test login and session================================================================================================
@blueprint_auth.route('/user_session_test')
def user_session_test():
    logger.debug(f"\n Login and Session testing: \n")
    user = current_user
    logger.debug(f"Current User:\n")
    try:
        logger.debug(f"id: {user.id}\n")
    except AttributeError as e:
        logger.debug(f"Except {e}: id: {user.get_id()}")
    try:
        logger.debug(f"is_auth: {user.is_authenticated}\n")
    except AttributeError as e:
        logger.debug(f"Except {e}: user_object: {user}")
    logger.debug(f"\n")
    current_session = session
    logger.debug(f"Current Session:\n")
    logger.debug(f"{current_session}")
    current_cookies = request.cookies
    logger.debug(f"Current Cookies:\n")
    logger.debug(f"{current_cookies}")
    logger.debug(f"\n :Login and Session testing\n")
    return redirect(url_for('index.index'))
# ======================================================================================================================


# WdraxUser view =======================================================================================================
@blueprint_auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # This is the landing page where users should be able to navigate to the following
    # - Make a new extract bundle
    # - Alter their API keys
    # - Anything else we add later
    if request.method == 'POST':
        if 'select_method' in request.form:
            return redirect(url_for('extract.select_method'))
        if 'change_api' in request.form:
            return redirect(url_for('auth.get_keys'))
        if 'go_to_extracts' in request.form:
            return redirect(url_for('extract.show_extracts'))
        if 'logout' in request.form:
            return redirect(url_for('auth.logout'))
        if 'view_graph' in request.form:
            return redirect(url_for('neo.show_graph'))
    elif request.method == 'GET':
        return render_template('profile.html', name=current_user.name)
# ======================================================================================================================


# GET for login pages===================================================================================================
@blueprint_auth.route('/login')
def login():
    # TODO: Add twitter login https://github.com/shalvah/twittersignin
    if current_user.is_authenticated:
        return redirect(url_for('auth.profile'))
    return render_template('login.html')


@blueprint_auth.route('/signup')
def signup():
    # TODO: Add twitter login https://github.com/shalvah/twittersignin
    return render_template('signup.html')


@blueprint_auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index.index'))


@blueprint_auth.route('/get_keys')
@login_required
def get_keys():
    return render_template('get_keys.html', endpoints=current_app.config['TWITTER_ENDPOINTS'])
# ======================================================================================================================


# POST for the login pages==============================================================================================
@blueprint_auth.route('/login_post', methods=['POST'])
def login_post():
    remember = True if request.form.get('remember') else False

    user = WdraxUser.query.filter_by(email=request.form.get('email')).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not user.check_password(request.form.get('password')):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))  # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    result = login_user(user, remember=remember)
    logger.debug(f"Login result is {result}")
    logger.debug(f"Current user localscope:appscope is {user.name}:{current_user.name}")
    logger.debug(f"Current user auth setting is localscope:appscope {user.is_authenticated}:{current_user.is_authenticated}")
    logger.debug(f"Session has {session}")
    next_page = session.get('next')
    logger.debug(f"next page is {next_page}")
    if next_page is None:
        logger.debug("Login successful.")
        if current_user.twitter_keys_set:
            next_page = url_for('auth.profile')
        else:
            next_page = url_for('auth.get_keys')
    elif not url_parse(next_page) or url_parse(next_page).netloc != '':
        if current_user.twitter_keys_set:
            next_page = url_for('auth.profile')
        else:
            next_page = url_for('auth.get_keys')
    return redirect(next_page)


@blueprint_auth.route('/signup_post', methods=['POST'])
def signup_post():
    email = request.form.get('email')

    # if this returns a user, then the email already exists in database
    user = WdraxUser.query.filter_by(email=email).first()
    if user:  # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = WdraxUser(email=email, name=request.form.get('name'))
    new_user.set_password(request.form.get('password'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('auth.login'))


@blueprint_auth.route('/get_keys', methods=['POST'])
@login_required
def get_keys_post():
    current_user.set_keys(request.form)
    return redirect(url_for('auth.profile'))
# ======================================================================================================================
