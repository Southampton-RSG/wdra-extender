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
