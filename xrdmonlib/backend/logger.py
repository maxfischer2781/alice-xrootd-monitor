from __future__ import division, absolute_import, print_function
import sys
import logging

import chainlet


@chainlet.funclet
def debug(value, fmt='%r', destination=sys.stderr):
    """Print the value to `destination` and pass it on unchanged"""
    print(fmt % value, file=destination)
    return value


@chainlet.genlet
def log(logger='xrdmonlib.debug', level=logging.CRITICAL):
    """Log the value to `logger` and pass it on unchanged"""
    _logger = logging.getLogger(logger)
    message = yield
    while True:
        _logger.log(level, message)
        message = yield message
