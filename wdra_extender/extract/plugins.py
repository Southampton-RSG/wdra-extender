"""Module containing tweet processing plugin loaders and structure."""

import abc
import logging
import os
import pathlib
import subprocess
import typing

from flask import current_app


class PluginBase(metaclass=abc.ABCMeta):
    """
    Base class for Python plugins to WDRAX.

    All Python plugins should inherit from this class
    """
    def __init__(self, tweets: typing.Iterable, tweets_file=None):
        self.tweets = tweets
        self.tweets_file = tweets_file

        current_app.logger.info('Starting plugin: %s', self)

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
    def log(msg):
        current_app.logger.log(level, msg)

    log('-- Plugin STDOUT')
    for line in proc.stderr.splitlines():
        log(line)
    log('-- End plugin STDOUT')

    log('-- Plugin STDERR')
    for line in proc.stdout.splitlines():
        log(line)
    log('-- End plugin STDERR')


def executable_plugin(filepath) -> typing.Callable:
    """Factory to construct an Executable Plugin from a filepath.

    An Executable Plugin is any executable program which processes
    the tweet data provided by it to WDRAX and produces a number
    of output files in the specified working directory.
    """
    def run(tweets_file: pathlib.Path = None, work_dir: pathlib.Path = None, twitter_key_dict: dict = None):
        """Run an executable file as a WDRAX plugin.

        The file is expected to save files in the working directory
        which will be included in the output zip file.
        """
        # Add plugin directory to environment so extra files can be used
        env = os.environ.copy()
        env['BIN'] = filepath.parent
        for key in {
                'TWITTER_CONSUMER_KEY', 'TWITTER_CONSUMER_SECRET',
                'TWITTER_ACCESS_TOKEN', 'TWITTER_ACCESS_TOKEN_SECRET'
        }:
            env[key.replace('TWITTER_', '')] = twitter_key_dict['search_tweets'][key[8:].lower()]

        current_app.logger.info(f'Executing plugin: {filepath.parent.name}')
        try:
            current_app.logger.debug(f'{filepath}, {tweets_file}')
            proc = subprocess.run([str(filepath), str(tweets_file)],
                                  cwd=str(work_dir),
                                  check=True,
                                  capture_output=True,
                                  env=env,
                                  text=True)

        except subprocess.CalledProcessError:
            # Process returned non-zero status
            current_app.logger.error('Plugin failed: %s', filepath.parent.name)
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

    @staticmethod
    def get_main_file(dir_path: pathlib.Path) -> pathlib.Path:
        """Find and validate the main file within a plugin directory."""
        main_files = list(dir_path.glob('main.*'))

        if len(main_files) == 1:
            plugin_path = main_files[0]
            if plugin_path.is_file() and os.access(plugin_path, os.X_OK):
                return plugin_path

            raise IOError('Plugin main.* file is not executable')

        if len(main_files) > 1:
            raise IOError('Plugin has more than one main.* file')
        
        raise IOError('Plugin has no main.* file')

    def load_plugins(self) -> typing.Dict[pathlib.Path, typing.Callable]:
        """Load plugins from the specified directories."""
        # Load executable files as plugins
        for directory in self.plugin_directories:
            current_app.logger.info('Loading plugins from directory: %s',
                                    directory)

            subdirs = sorted(p for p in directory.iterdir() if p.is_dir())
            for dir_path in subdirs:
                try:
                    plugin_path = self.get_main_file(dir_path)

                except IOError as exc:
                    current_app.logger.error('Error loading plugin %s: %s', dir_path, str(exc))
                    continue

                current_app.logger.info('Loaded executable plugin: %s',
                                        dir_path.name)
                self.plugins[dir_path] = executable_plugin(plugin_path)

        return self.plugins
