"""
Various helper utilities
"""
from __future__ import division, absolute_import
import os
import ast
import sys
import inspect
import socket


from . import compat


def validate_process(pid, name=None):
    """
    Check whether there is a process with `pid` and `name`

    :param pid: pid of the running process
    :param name: name of the running process
    :type name: str or None
    :returns: whether there is a process with the given name and pid
    :rtype: bool
    """
    try:
        with open(os.path.join('/proc', str(pid), 'comm')) as proc_comm:
            proc_name = next(proc_comm).strip()
    except (OSError, IOError):
        return False
    return name is None or name == proc_name


def safe_eval(literal):
    """
    Attempt to evaluate a literal value

    Safely performs the evaluation of a literal. If the literal is not valid,
    it is assumed to be a regular string and returned unchanged.

    :param literal: literal to evaluate, e.g. `"1.0"` or `"{'foo': 3}"`
    :type literal: str
    :return: evaluated or original literal
    """
    try:
        return ast.literal_eval(literal)
    except (ValueError, SyntaxError):
        return literal


def get_signature(target):
    """
    Get a pretty formatted call signature, e.g. `'(bar, foo:int=3, *args, chloe=15, **kwargs)'`

    :param target:
    :return: call signature of `target`
    :rtype: str
    """
    if sys.version_info > (3,):
        return str(inspect.signature(target))
    if hasattr(target, '__init__'):
        target = target.__init__
    argspec = inspect.getargspec(target)
    signature = []
    args = argspec.args[1:] if argspec.args and argspec.args[0] == 'self' else argspec.args
    if argspec.defaults is None:
        signature.extend(args)
    else:
        if len(args) > len(argspec.defaults):
            signature.extend(args[:-len(argspec.defaults)])
        signature.extend('%s=%r' % (arg, default) for arg, default in zip(
            args[-len(argspec.defaults):], argspec.defaults)
        )
    if argspec.varargs:
        signature.append('*' + argspec.varargs)
    if argspec.keywords:
        signature.append('**' + argspec.keywords)
    return '(%s)' % ', '.join(signature)


_socket_flavours = {
        'UDP': (socket.AF_INET, socket.SOCK_DGRAM),
        'TCP': (socket.AF_INET, socket.SOCK_STREAM),
        'UDP6': (socket.AF_INET6, socket.SOCK_DGRAM),
        'TCP6': (socket.AF_INET6, socket.SOCK_STREAM),
        'UNIXGRAM': (socket.AF_UNIX, socket.SOCK_DGRAM),
        'UNIX': (socket.AF_UNIX, socket.SOCK_STREAM),
    }


def simple_socket(flavour):
    """
    A thin abstraction around `socket.socket`. Supports simple socket type
    selection via `flavour`.
    """
    if isinstance(flavour, compat.string_type):
        flavour = _socket_flavours[flavour.upper()]
    return socket.socket(*flavour)
