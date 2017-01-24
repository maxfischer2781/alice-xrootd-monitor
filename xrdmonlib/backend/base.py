from __future__ import division, absolute_import
import weakref


class ChainElement(object):
    """
    An element in a report chain

    Each element may fork to an arbitrary number of elements. However, there may
    be only one parent element. Elements for a chain, passing along data via
    :py:meth:`~.send`.
    """
    def __init__(self, *children):
        self._parent = None
        self._children = list(children)

    @property
    def root(self):
        """root element leading to this element"""
        parent = self
        while True:
            next_parent = parent.parent
            if next_parent is not None:
                parent = next_parent
            else:
                break
        return parent

    @property
    def parent(self):
        """Parent element"""
        if self._parent is None:
            return None
        return self._parent()

    @parent.setter
    def parent(self, value):
        self._parent = weakref.ref(value)

    def __rshift__(self, children):
        """Support `self >> element` and `self >> (element, element)`"""
        # fork to multiple consumers
        if isinstance(children, tuple):
            for child in children:
                self >> child
        # add individual consumer
        else:
            self._children.append(children)
            children.parent = self
        return children

    def __lshift__(self, parent):
        """Support `self << chain` and `self << element`"""
        # fork to multiple children
        if isinstance(parent, tuple):
            raise TypeError('%s cannot have more than one parent' % self.__class__.__name__)
        else:
            parent >> self
        return parent

    def send(self, value=None):
        """Send a value to this element"""
        for child in self._children:
            child.send(value)

    def _elem_repr(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(
            '%s=%r' % (key, value) for key, value in vars(self).items() if key[0] != '_'
        ))

    def __repr__(self):
        if not self._children:
            return self._elem_repr()
        elif len(self._children) == 1:
            return '%s >> %r' % (self._elem_repr(), self._children[0])
        else:
            return '%s >> (%s)' % (self._elem_repr(), ', '.join(repr(elem) for elem in self._children))


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
