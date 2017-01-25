from __future__ import division, absolute_import
import os
import sys
import argparse
import logging.handlers
import textwrap
import platform

from . import core
from . import compat
from .backend.base import ChainStart


class ArgparseConfigHelp(argparse.Action):
    """Print help on configuration via argparse"""
    def __init__(self, *args, **kwargs):
        if 'help' not in kwargs:
            kwargs['help'] = 'show the config help message and exit'
        kwargs['nargs'] = 0
        argparse.Action.__init__(self, *args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_usage()
        self._print_help(self._get_usehelp())
        parser.exit()

    @staticmethod
    def _print_help(help_str):
        print(textwrap.dedent(help_str))

    def _get_usehelp(self):
        return """\

        The configuration file must set the port to listen for reports and a
        chain for processing reports. A simple configuration looks like this:

            port = 12345
            reports >> LogFile("/tmp/xrdmon.log")

        The report chain can use objects to transform or digest reports. The operation
        `a >> b` chains two elements a and b. Doing `a >> (b, c)` forks the report
        stream from a to both b and c.

        Note that the configuration file is actually a Python file, with some names
        already provided. The available short names are listed in debug output.
        """


CLI = argparse.ArgumentParser(description='XRootD monitoring report multiplexer and logger')
CLI.add_argument('config', help='path to configuration file', metavar='CONFIGPATH')
CLI.add_argument('--config-help', action=ArgparseConfigHelp)
CLI_LOG = CLI.add_argument_group(title='debug logging facilities', description='See https://docs.python.org/2/library/logging.html for meaning of values')
CLI_LOG.add_argument('-l', '--log-level', help='logging verbosity, numeric or name', default='WARNING')
CLI_LOG.add_argument('-f', '--log-format', help='logging message format', default='%(asctime)s (%(process)d) %(levelname)8s: %(message)s')
CLI_LOG.add_argument('-d', '--destinations', help='logging destinations, as file path or stderr/stdout', nargs='*', default=['stderr'])


def cli_log_config(log_level, log_format, destinations, **_):
    """
    Configure logging from CLI options

    :param log_level: logging verbosity
    :type log_level: int or str
    :param log_format: format string for messages
    :type log_format: str
    :param destinations: where to send log message to
    :type destinations: tuple[str]

    Each element in `destinations` must be either a stream name
    (`"stdout"` or `"stdout"`), or it is interpreted as a file name.
    """
    try:
        log_level = getattr(logging, log_level.upper())
    except AttributeError:
        pass
    log_level = int(log_level)
    root_handlers = logging.getLogger().handlers[:]
    logging.basicConfig(format=log_format, level=log_level)
    root_fmt = logging.getLogger().handlers[0].formatter
    # we add handlers by ourselves to use appropriate classes
    # during initialisation, use the default handler in case something goes wrong
    for destination in destinations:
        if destination == 'stderr':
            root_handlers.append(logging.StreamHandler(sys.stderr))
        elif destination == 'stdout':
            root_handlers.append(logging.StreamHandler(sys.stdout))
        else:
            if not os.path.isdir(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
            root_handlers.append(logging.handlers.WatchedFileHandler(filename=destination))
        root_handlers[-1].setFormatter(root_fmt)
    logging.getLogger().handlers[:] = root_handlers


class PyConfiguration(object):
    """
    Configuration file interface for Python configuration files

    :param map_nicknames: tuples as appropriate for :py:meth:`map_backend`
    """
    def __init__(self, *map_nicknames):
        self.backends = {}
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        for backend in map_nicknames:
            self.map_bickname(*backend)  # expecting (nickname: str, module: str, name: str)

    def map_bickname(self, nickname, module, name):
        """
        Add shorthand name for objects available in configuration
        """
        try:
            __import__(module)
            module = sys.modules[module]
            cls = module
            for sname in name.split('.'):
                cls = getattr(cls, sname)
        except ImportError as err:
            self._logger.info('failed to load backend module %s: %s' % (module, err))
        except NameError as err:
            self._logger.info('failed to load backend object %s.%s: %s' % (module, name, err))
        else:
            self.backends[nickname] = cls
            self._logger.debug('added config nickname %s => %s.%s', nickname, cls.__module__, cls.__name__)

    def configure_core(self, config_path):
        """Initialize a :py:class:`~.core.Core` from a configuration file"""
        self._logger.info('configuration interpreter: %s %s', platform.python_implementation(), platform.python_version())
        self._logger.info('using config nicknames %s', ', '.join(self.backends))
        # namespace available in the config file
        config_namespace = self.backends.copy()
        config_namespace['reports'] = ChainStart('ReportStream')
        config_namespace['logging'] = logging
        self._logger.info('running configuration file %r', config_path)
        config_dict = compat.run_path(
            config_path,
            init_globals=config_namespace,
            run_name=os.path.basename(config_path)
        )
        kwarg_aliases = {'report_port': ['port'], 'backends': ['reports', 'backends']}
        core_kwargs = {}
        for keyword, aliases in kwarg_aliases.items():
            for alias in aliases:
                try:
                    value = config_dict[alias]
                except KeyError:
                    continue
                else:
                    core_kwargs[keyword] = value
                    self._logger.info('configuration: %s => %r', keyword, value)
                    break
            else:
                raise ValueError('missing config value: %s (aliases: %s)')
        monitor_core = core.Core(**core_kwargs)
        return monitor_core
