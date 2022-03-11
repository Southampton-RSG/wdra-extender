from inspect import signature, getmembers, isfunction
import logging
import typing

from flask import current_app, Blueprint, jsonify, flash, redirect, url_for

blueprint_tools = Blueprint("tools", __name__, url_prefix='/wdrax/tools')


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
        current_app.logger.debug(f"Function Signature:\n{outer_sig}")
        new_kwargs = {}
        for param in outer_sig.parameters.values():
            if param.kind in [param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY, param.VAR_KEYWORD]:
                if param.name in kwargs.keys():
                    new_kwargs[param.name] = kwargs[param.name]
        current_app.logger.debug(f"Old Kwargs:\n{kwargs}\n"
                                 f"New Kwargs:\n{new_kwargs}")
        return func(*args, **new_kwargs)
    return wrapper
# ======================================================================================================================


# Tools for working with/on background tasks============================================================================
def get_task_fun(task_id):
    from .tasks import build_extract, rebuild_extract
    # This is a workaround as getmembers(tasks, isfunction) wont return the celery decorated values using the inspect
    # libraries is the preferred way to do this.
    task_list = [build_extract, rebuild_extract]
    for task_fun in task_list:
        try:
            task = task_fun.AsyncResult(task_id)
        except AttributeError:
            task = None
            pass
    return task


@blueprint_tools.route('/task/status/<task_id>')
def task_status(task_id):
    task = get_task_fun(task_id)

    task_state_dict = {
        'PENDING': [],
        'STARTING': ['task_type'],
        'COLLECTING': ['collected'],
        'RATE_LIMITING': ['tries', 'sleep_start', 'sleep'],
        'SUCCESS': [],
        'FAILURE': ['error']
    }
    response = None
    if task is not None:
        for task_state in task_state_dict.keys():
            if task.state == task_state:
                # construct response from meta
                if task.state not in ['PENDING', 'SUCCESS']:
                    response = {}
                    try:
                        response = {key: value for key, value in task.info.items()}
                        response['state'] = task.state
                    except AttributeError as e:
                        response = {'state': "An Error occurred while fetching Tweets.  "
                                             "Please check the validity of you Twitter credentials.\n"
                                             f"Error log: {e}"}
                else:
                    response = {'state': task.state}
    else:
        response = {'state': 'No task found'}
    if response is None:
        response = {'state': "Task found but has no response value"}
    return jsonify(response)


@blueprint_tools.route('/task/kill/<task_id>')
def kill_task(task_id):
    task = get_task_fun(task_id)
    if task is not None:
        task.revoke(terminate=True)
        message = f"Task {task_id} revoked"
    else:
        message = f"Task {task_id} not found"
    flash(message)
    return redirect(url_for('extract.delete_extract', extract_uuid=task_id))
# ======================================================================================================================
