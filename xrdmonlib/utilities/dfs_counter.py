import socket
import os
import hashlib
import filelock
import glob
import time
import threading
import logging
import weakref
import operator


# actually a method of DFSCounter
# must be separate to allow garbage collection of self
def _count_updater(self):
    """separate counter loop to regularly check/verify state"""
    assert isinstance(self, weakref.ProxyTypes), "counter thread must receive weakref'd self to be collectible"
    self._logger.info('acquiring %r @ %r', self.__repr__(), self._marker_path)
    marker_path = self._marker_path
    thread_shutdown = self._thread_shutdown
    with self._host_lock:
        while not thread_shutdown.is_set():
            try:
                with open(self._marker_path, 'wb') as marker:
                    marker.write('%s %s' % (self._host_identifier, os.getpid()))
                self._count_value = self._get_count()
                self._thread_shutdown.wait(self.timeout / 4)
            except ReferenceError:
                break
            except Exception as err:
                self._logger.info('failed updating %r: %s', self.__repr__(), err)
        if os.path.exists(marker_path) and os.path.isfile(marker_path):
            os.unlink(marker_path)


class DFSCounter(object):
    """
    Counter for processes accessing the same Distributed File System

    :param shared_path: path used for synchronisation
    :type shared_path: str
    :param timeout: maximum age of synchronisation in seconds before assuming stale processes
    :type timeout: int or float

    This class pretends to be an integer for all intents and purposes.
    """
    def __init__(self, shared_path, timeout=300):
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self.shared_path = shared_path
        self.timeout = timeout
        self._host_identifier = socket.getfqdn()
        self._marker_path = self._get_marker_path(hashlib.sha1(self._host_identifier).hexdigest())
        self._host_lock = filelock.FileLock(self._marker_path + '.lock')
        self._thread_shutdown = threading.Event()
        self._thread_shutdown.clear()
        self._count_value = 0
        self._thread = threading.Thread(target=_count_updater, args=(weakref.proxy(self),))
        self._thread.start()

    def _get_marker_path(self, identifier):
        return '%sdfsc-%s.csv' % (self.shared_path, identifier)

    # cross host counting
    def _get_count(self):
        min_age = time.time() - self.timeout
        return sum(1 for file_path in glob.iglob(self._get_marker_path('*')) if os.stat(file_path).st_mtime > min_age)

    def release(self):
        """Release the underlying resource"""
        self._thread_shutdown.set()

    def __del__(self):
        self._thread_shutdown.set()

    # representation
    def __str__(self):
        return str(int(self))

    def __repr__(self):
        return '<%s(shared_path=%s, timeout=%s), value=%d>' % (
            type(self).__name__, self.shared_path, self.timeout, self._count_value
        )

    # overriding __class__ at the instance level does not work, but changing the slot wrapper does
    @property
    def __class__(self):
        return int

    # comparisons
    def __lt__(self, other):
        return int(self) < other

    def __le__(self, other):
        return int(self) <= other

    def __eq__(self, other):
        return int(self) == other

    def __ne__(self, other):
        return int(self) != other

    def __gt__(self, other):
        return int(self) > other

    def __ge__(self, other):
        return int(self) >= other

    # value may change, not hashable
    __hash__ = None

    # number interface
    def __int__(self):
        return self._count_value

    __index__ = __int__

    def __complex__(self):
        return complex(int(self))

    def __float__(self):
        return float(int(self))

    def __long__(self):
        return long(int(self))

    def __round__(self, ndigits):
        return round(int(self), ndigits=ndigits)

    def __bytes__(self):
        return bytes(int(self))

    def __oct__(self):
        return oct(int(self))

    def __hex__(self):
        return hex(int(self))

    def __neg__(self):
        return -int(self)

    def __pos__(self):
        return int(self)

    def __abs__(self):
        return abs(int(self))

    def __invert__(self):
        return ~int(self)

    def __add__(self, other):
        return int(self) + other

    def __radd__(self, other):
        return other + int(self)

    def __sub__(self, other):
        return int(self) - other

    def __rsub__(self, other):
        return other - int(self)

    def __mul__(self, other):
        return int(self) * other

    def __rmul__(self, other):
        return other * int(self)

    def __floordiv__(self, other):
        return int(self) // other

    def __rfloordiv__(self, other):
        return other // int(self)

    def __mod__(self, other):
        return int(self) % other

    def __rmod__(self, other):
        return other % int(self)

    def __divmod__(self, other):
        return divmod(int(self), other)

    def __rdivmod__(self, other):
        return divmod(other, int(self))

    def __pow__(self, other, modulo):
        return pow(int(self), other, modulo)

    def __rpow__(self, other):
        return other ** int(self)

    def __lshift__(self, other):
        return int(self) << other

    def __rlshift__(self, other):
        return other << int(self)

    def __rshift__(self, other):
        return int(self) >> other

    def __rrshift__(self, other):
        return other >> int(self)

    def __and__(self, other):
        return int(self) & other

    def __rand__(self, other):
        return other & int(self)

    def __xor__(self, other):
        return int(self) ^ other

    def __rxor__(self, other):
        return other ^ int(self)

    def __or__(self, other):
        return int(self) | other

    def __ror__(self, other):
        return other | int(self)

    def __div__(self, other):
        return operator.div(int(self), other)

    def __rdiv__(self, other):
        return operator.div(other, int(self))

    def __truediv__(self, other):
        return operator.truediv(int(self), other)

    def __rtruediv__(self, other):
        return operator.truediv(other, int(self))
