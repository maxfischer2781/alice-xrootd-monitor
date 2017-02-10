"""
Basic Elements for creating report chains
"""
from __future__ import division, absolute_import

import chainlet


class ChainElement(chainlet):
    """
    An element in a report chain

    Each element may fork to an arbitrary number of elements. However, there may
    be only one parent element. Elements for a chain, passing along data via
    :py:meth:`~.send`.
    """


class ChainStart(ChainElement):
    """
    First element in a chain

    :param nice_name: name to display as first element of a chain
    :type nice_name: str
    """
    def __init__(self, nice_name):
        super(ChainStart, self).__init__()
        self.nice_name = nice_name

    def _elem_repr(self):
        return self.nice_name
