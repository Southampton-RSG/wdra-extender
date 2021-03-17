"""
Module containing the index view
"""

from flask import Blueprint, render_template, redirect, request, url_for
from ..extract.tools import ContextProxyLogger
# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)

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
    elif request.method == 'GET':
        return render_template('index.html')
