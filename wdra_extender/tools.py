from inspect import signature, getmembers, isfunction
import logging
import typing

from . import tasks
from flask import current_app, Blueprint, jsonify

blueprint_tools = Blueprint("tools", __name__)


# Tool for creating an appropriate logger===============================================================================
class ContextProxyLogger(logging.Logger):
    """Logger proxy for when we may be inside or outside of the Flask context.

    If inside the Flask context, redirect to the Flask app logger.
    If outside the Flask context, act as a default Python logger.
    """
    def __getattribute__(self, name: str) -> typing.Any:
        try:
            return current_app.logger.__getattribute__(name)

        except RuntimeError as exc:
            if 'outside of application context' in str(exc):
                return super().__getattribute__(name)

            raise


# Function decorator to parse kwargs and remove any that dont appear in the function definition ========================
def get_valid_kwargs(func):
    def wrapper(*args, **kwargs):
        outer_sig = signature(func)
        new_kwargs = {}
        for param in outer_sig.parameters.values():
            if param.kind in [param.KEYWORD_ONLY, param.VAR_KEYWORD]:
                if param.name in kwargs.keys():
                    new_kwargs[param.name] = kwargs[param.name]
        return func(*args, **new_kwargs)
    return wrapper
# ======================================================================================================================


# ======================================================================================================================
@blueprint_tools.route('/status/<task_id>')
def task_status(task_id):
    for task_fun_name, task_fun_value in getmembers(tasks, isfunction):
        task_fun = getattr(tasks, task_fun_name)
        try:
            task = task_fun.AsyncResult(task_id)
        except AttributeError:
            task = None
            pass

    task_state_dict = {
        'PENDING': [],
        'STARTING': ['task_type'],
        'COLLECTING': ['collected'],
        'RATE_LIMITING': ['tries', 'sleep_start', 'sleep'],
        'FAILED': ['error']
    }
    response = None
    if task is not None:
        for task_state in task_state_dict.keys():
            if task.state == task_state:
                # construct response from meta
                response = {key: value for key, value in task.info}
                response['state'] = task.state
    else:
        response = {'state': 'No task found'}
    if response is None:
        response = {'state': "Task found but has no response value"}
    return jsonify(response)
# ======================================================================================================================
