from __future__ import print_function
import sys
import yaml
import argparse
import textwrap

from . import core


class ConfigError(BaseException):
    """Incorrect Configuration Content"""
    pass


class YamlConfig(object):
    """
    Parser for Configurations in YAML format to a :py:class:`~core.Core` instance

    :param backend_nicks: short names for individual backends
    :type backend_nicks: dict[str, object]
    """
    def __init__(self, backend_nicks=None):
        self.backend_nicks = {} if backend_nicks is None else backend_nicks

    def parse_path(self, path):
        raw_data = self._raw_parse_path(path)
        if not isinstance(raw_data, dict):
            raise ConfigError("configuration top-level must be a mapping")
        core_kwargs = self._make_corekwargs(raw_data)
        return core.Core(**core_kwargs)

    @staticmethod
    def _raw_parse_path(path):
        with open(path) as yaml_config:
            raw_data = yaml.parse(yaml_config)
        return raw_data

    def _make_corekwargs(self, raw_data):
        kwargs = raw_data.copy()
        try:
            kwargs.pop('backends')
        except KeyError:
            raise ConfigError('configuration requires "backends" to be defined')
        kwargs['backends'] = self._make_backends(raw_data)
        return kwargs

    def _make_backends(self, raw_data):
        """Create all backends"""
        backend_dicts = raw_data.pop('backends', [])
        if isinstance(backend_dicts, dict):
            backend_dicts = [backend_dicts]
        return [self._instantiate_backend(cls_dict) for cls_dict in backend_dicts]

    def _get_backend_class(self, cls_dict):
        """Fetch the class `cls_dict['class']`, optionally from `cls_dict['import']`"""
        try:
            cls_name = cls_dict.pop('class')
        except KeyError:
            raise ConfigError('backend type must be specified via "class"')
        cls_module = cls_dict.pop('import', None)
        if cls_module is None:
            try:
                cls = self.backend_nicks[cls_name]
            except KeyError:
                raise ConfigError('backend type "class" must be a nickname if "import" is not set')
        else:
            try:
                # __import__('foo.bar.baz') will only return 'foo'!
                __import__(cls_module)
                module = sys.modules[cls_module]
                cls = getattr(module, cls_name)
            except Exception as err:
                raise ConfigError('failed to load class=%s from import=%s: %s' % (cls_name, cls_module, err))
        return cls

    def _instantiate_backend(self, cls_dict):
        if not isinstance(cls_dict, dict):
            raise ConfigError("configuration for each backend must be a mapping")
        cls = self._get_backend_class(cls_dict)
        try:
            return cls(**cls_dict)
        except Exception as err:
            raise ConfigError('failed to instantiate %s: %s' % (cls, err))


class ArgparseConfigHelp(argparse.Action):
    def __init__(self, *args, **kwargs):
        self.backend_nicks = kwargs.pop('backend_nicks', {})
        kwargs['nargs'] = '?'
        if 'help' not in kwargs:
            kwargs['help'] = 'Get help on backends, as nickname or name[:module]'
        if 'metavar' not in kwargs:
            kwargs['metavar'] = 'NAME[:MODULE]'
        argparse.Action.__init__(self, *args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if not values:
            self._print_help(self._get_usehelp())
        elif values == 'core':
            self._print_help(self._get_corehelp())
        else:
            self._print_help(self._get_backendhelp(values))
        parser.exit()

    @staticmethod
    def _print_help(help_str):
        print(textwrap.dedent(help_str))

    def _get_usehelp(self, option_string=None):
        return textwrap.dedent("""\
        Configuration must provide settings nested as they are passed as
        arguments. Backends can be used from the package as

            class: <nick name>

        or from any plugin module as

            class: <class name>
            import: <dotted module path>

        Usage for help on topics
        %(ostr)s  core          : monitor core
        %(ostr)s <nick>         : builtin backend via nickname
        %(ostr)s <class:module> : plugin backend via class and module

        Available nick names:
        %(nicks)s
        """ % {
            'ostr': option_string or self.option_strings[0],
            'nicks': ', '.join(self.backend_nicks)
        })

    @staticmethod
    def _get_corehelp():
        return core.Core.__doc__

    def _get_backendhelp(self, identifier):
        return self._get_class(identifier).__doc__

    def _get_class(self, identifier):
        if ':' not in identifier:
            try:
                identifier = self.backend_nicks[identifier.lower()]
            except KeyError:
                raise ConfigError('failed to load nick=%s: Unknown nick name' % identifier)
        cls_name, cls_module = identifier.split(':', 1)
        try:
            # __import__('foo.bar.baz') will only return 'foo'!
            __import__(cls_module)
            module = sys.modules[cls_module]
            return getattr(module, cls_name)
        except Exception as err:
            raise ConfigError('failed to load class=%s, import=%s: %s' % (cls_name, cls_module, err))
