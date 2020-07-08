import abc
import importlib
import logging
import os
import pathlib
import subprocess
import typing

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class PluginBase(metaclass=abc.ABCMeta):
    """
    Base class for Python plugins to WDRAX.

    All Python plugins should inherit from this class
    """
    def __init__(self, tweets: typing.Iterable, tweets_file=None):
        self.tweets = tweets
        self.tweets_file = tweets_file

        logger.info('Starting plugin: %s', self)

    @abc.abstractmethod
    def run(self, tweets: typing.Iterable):
        pass

    def __repr__(self) -> str:
        """Representation of plugin for logging purposes."""
        return type(self).__name__


def executable_plugin(filepath):
    def run(tweets: typing.Iterable = None, tweets_file: pathlib.Path = None):
        logger.info('Executing plugin: %s', filepath)
        proc = subprocess.run([filepath, tweets_file],
                              capture_output=True,
                              text=True)

        logger.info('-- Plugin STDERR')
        for line in proc.stderr.splitlines():
            logger.info(line)
        logger.info('-- End plugin STDERR')

        return proc.stdout

    return run


class PluginCollection:
    def __init__(self, plugin_directories: typing.Iterable[pathlib.Path]):
        self.plugin_directories = plugin_directories
        self.plugins = {}

    def load_plugins(self) -> typing.Dict[pathlib.Path, typing.Callable]:
        # TODO detect plugins in directory

        # Load executable files as plugins
        for directory in self.plugin_directories:
            logger.info('Loading plugins from directory: %s', directory)

            for filepath in directory.iterdir():
                if filepath.is_file() and os.access(filepath, os.X_OK):
                    logger.info('Found executable plugin: %s', filepath)
                    self.plugins[filepath] = executable_plugin(filepath)

        return self.plugins
