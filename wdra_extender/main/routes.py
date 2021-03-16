"""
Module containing the index view
"""

from flask import Blueprint, render_template, redirect, request, url_for
from ..extract.tools import ContextProxyLogger
# Logger safe for use inside or outside of Flask context
logger = ContextProxyLogger(__name__)

blueprint_index = Blueprint("index", __name__)


# Both routes are required for cross compatibility on RHEL8 and CentOS 8, without both '...:8000/' will work on RHEL8
# and '...8000/index' will work on CentOS8. With both routes '...:8000/' works on both and '...:8000/index on neither!
# TODO: get both '/index' and '/' working. Issue #12
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