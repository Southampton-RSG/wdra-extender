import abc
import logging

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class PluginBase(metaclass=abc.ABCMeta):
    """
    Base class for Python plugins to WDRAX.

    All Python plugins should inherit from this class
    """
    def __init__(self, tweets):
        self.tweets = tweets

        logger.info('Starting plugin: %s', self)

    @abc.abstractmethod
    def run(self):
        pass

    def __repr__(self) -> str:
        """Representation of plugin for logging purposes."""
        return type(self).__name__
