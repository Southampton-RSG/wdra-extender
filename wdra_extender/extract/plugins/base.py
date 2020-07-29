"""Module containing tweet processing plugin loaders and structure."""

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
    def run(self,
            tweets: typing.Iterable = None,
            tweets_file: pathlib.Path = None,
            work_dir: pathlib.Path = None):
        """Execute this plugin.

        The plugin is expected to save files in the working directory
        which will be included in the output zip file.
        """

    def __repr__(self) -> str:
        """Representation of plugin for logging purposes."""
        return type(self).__name__


def log_proc_output(proc: subprocess.CompletedProcess,
                    level: int = logging.INFO) -> None:
    """Log stdout and stderr of a subprocess."""
    logger.log('-- Plugin STDOUT', level=level)
    for line in proc.stderr.splitlines():
        logger.log(line, level=level)
    logger.log('-- End plugin STDOUT', level=level)

    logger.log('-- Plugin STDERR', level=level)
    for line in proc.stdout.splitlines():
        logger.log(line, level=level)
    logger.log('-- End plugin STDERR', level=level)


def executable_plugin(filepath) -> typing.Callable:
    """Factory to construct an Executable Plugin from a filepath.

    An Executable Plugin is any executable program which processes
    the tweet data provided by it to WDRAX and produces a number
    of output files in the specified working directory.
    """
    def run(tweets: typing.Iterable = None,
            tweets_file: pathlib.Path = None,
            work_dir: pathlib.Path = None):
        """Run an executable file as a WDRAX plugin.

        The file is expected to save files in the working directory
        which will be included in the output zip file.
        """
        # Add plugin directory to environment so extra files can be used
        env = os.environ.copy()
        env['BIN'] = filepath.parent

        logger.info('Executing plugin: %s', filepath)
        try:
            proc = subprocess.run([filepath, tweets_file],
                                  cwd=work_dir,
                                  check=True,
                                  capture_output=True,
                                  env=env,
                                  text=True)

        except subprocess.CalledProcessError:
            # Process returned non-zero status
            logger.error('Plugin failed: %s', filepath)
            log_proc_output(proc, level=logging.ERROR)

            raise

        else:
            log_proc_output(proc, level=logging.DEBUG)

        return proc.stdout

    return run


class PluginCollection:
    """Load plugins from one or multiple directories."""
    def __init__(self, plugin_directories: typing.Iterable[pathlib.Path]):
        self.plugin_directories = [
            d.resolve() for d in plugin_directories if d.is_dir()
        ]
        self.plugins = {}

    def load_plugins(self) -> typing.Dict[pathlib.Path, typing.Callable]:
        """Load plugins from the specified directories."""
        # TODO detect plugins in directory

        # Load executable files as plugins
        for directory in self.plugin_directories:
            logger.info('Loading plugins from directory: %s', directory)

            for filepath in directory.iterdir():
                if filepath.is_file() and os.access(filepath, os.X_OK):
                    logger.info('Found executable plugin: %s', filepath)
                    self.plugins[filepath] = executable_plugin(filepath)

        return self.plugins
