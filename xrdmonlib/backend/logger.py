from __future__ import division, absolute_import, print_function
import sys

import chainlet


@chainlet.FunctionLink.linklet
def debug(value, destination=sys.stderr):
    """Print the value to `destination` and pass it on unchanged"""
    print()
    print('Fooo!!!!', value, file=destination)
    print()
    return value
