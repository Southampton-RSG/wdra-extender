from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse

from wdra_extender.extensions import db
from .models import WdraxUser
from ..extract.tools import ContextProxyLogger
# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)

blueprint_auth = Blueprint('auth', __name__)


@blueprint_auth.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('extract.profile'))
    return render_template('login.html')


@blueprint_auth.route('/signup')
def signup():
    return render_template('signup.html')


@blueprint_auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('extract.index'))


@blueprint_auth.route('/get_keys')
@login_required
def get_keys():
    return render_template('get_keys.html')


@blueprint_auth.route('/login', methods=['POST'])
def login_post():
    remember = True if request.form.get('remember') else False

    user = WdraxUser.query.filter_by(email=request.form.get('email')).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not user.check_password(request.form.get('password')):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))  # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    next_page = request.args.get('next')
    if next_page is None:
        if current_user.twitter_keys_set:
            next_page = url_for('extract.profile')
        else:
            next_page = url_for('auth.get_keys')
    elif not url_parse(next_page) or url_parse(next_page).netloc != '':
        if current_user.twitter_keys_set:
            next_page = url_for('extract.profile')
        else:
            next_page = url_for('auth.get_keys')
    return redirect(next_page)


@blueprint_auth.route('/signup', methods=['POST'])
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
    """current_user.bearer_token = request.form.get('bearer_token')
    current_user.consumer_key = request.form.get('consumer_key')
    current_user.consumer_secret = request.form.get('consumer_secret')
    current_user.access_token = request.form.get('access_token')
    current_user.access_token_secret = request.form.get('access_token_secret')"""
    current_user.set_keys(request.form)
    return redirect(url_for('extract.profile'))
