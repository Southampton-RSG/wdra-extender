"""
Module containing the index view
"""

from flask import Blueprint, render_template, redirect, request, url_for


blueprint_index = Blueprint("index", __name__)


@blueprint_index.route('/', methods=['GET', 'POST'])
@blueprint_index.route('/index', methods=['GET', 'POST'])
def index():
    """Static page where users will land when first accessing WDRA-Extender."""
    if request.method == 'POST':
        if 'login' in request.form:
            return redirect(url_for('auth.login'))
        if 'sign_up' in request.form:
            return redirect(url_for('auth.signup'))
        if 'neo_test' in request.form:
            return redirect(url_for('neo.get_graph'))
    elif request.method == 'GET':
        return render_template('index.html')
