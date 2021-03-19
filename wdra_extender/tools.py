from inspect import signature
import logging
import typing

from flask import current_app


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
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                if param in kwargs:
                    new_kwargs[param] = kwargs[param]
        return func(*args, **new_kwargs)
    return wrapper
# ======================================================================================================================
