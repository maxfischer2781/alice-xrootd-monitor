from __future__ import division, absolute_import
import re

from . import base


class RegexFilter(base.ChainElement):
    """
    Filter report keys according to a regular expression

    :param whitelist: regular expression for keys to keep
    :type whitelist: str or None
    :param blacklist: regular expression for keys to delete
    :type blacklist: str or None

    By default, both `whitelist` and `blacklist` act permissive: all keys
    are kept. If `whitelist` is set, any key must match it in order to be kept.
    If `blacklist` is set, any key matching it is deleted. If both are used,
    keys are only kept if they match `whitelist` and do *not* match `blacklist`.
    """
    def __init__(self, blacklist=None, whitelist=None):
        super(RegexFilter, self).__init__()
        self._whitelist = None
        self._blacklist = None
        self._is_valid = None
        # cache for keys identified to keep as
        # keys will usually be static over reports, so we cache the results of validation
        self._keep_keys = {}  # key: str => keep: bool
        self.whitelist = whitelist
        self.blacklist = blacklist

    @property
    def whitelist(self):
        """Regular expression for keys to keep"""
        return self._whitelist

    @whitelist.setter
    def whitelist(self, value):
        if value != self._whitelist:
            self._whitelist = value
            self._make_filter()

    @property
    def blacklist(self):
        """Regular expression for keys to delete"""
        return self._blacklist

    @blacklist.setter
    def blacklist(self, value):
        if value != self._blacklist:
            self._blacklist = value
            self._make_filter()

    def _make_filter(self):
        self._keep_keys = type(self._keep_keys)()
        if self._whitelist is not None and self._blacklist is not None:
            whitelist_search = re.compile(self._whitelist).search
            blacklist_search = re.compile(self._blacklist).search
            def is_valid(key):
                return whitelist_search(key) is not None and blacklist_search(key) is None
        elif self._whitelist is not None:
            whitelist_search = re.compile(self._whitelist).search
            def is_valid(key):
                return whitelist_search(key) is not None
        elif self._blacklist is not None:
            blacklist_search = re.compile(self._blacklist).search
            def is_valid(key):
                return blacklist_search(key) is None
        else:
            is_valid = None
        self._is_valid = is_valid

    def send(self, report=None):
        """Filter and pass on a report"""
        if self._is_valid is not None:
            _keep_keys = self._keep_keys
            new_report = {}
            for key in report:
                try:
                    if _keep_keys[key]:
                        new_report[key] = report[key]
                except KeyError:
                    if self._is_valid(key):
                        _keep_keys[key] = True
                        new_report[key] = report[key]
                    else:
                        _keep_keys[key] = True
        super(RegexFilter, self).send(report)

    def _elem_repr(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(
            '%s=%r' % (key, getattr(self, key)) for key in ('whitelist', 'blacklist')
        ))


class FormatTransform(base.ChainElement):
    """
    Transform report keys according to a format string

    :param report_fmt: a Python printf style format string
    :type report_fmt: str

    The `report_fmt` is applied to each key in a report. The name of the
    current key is available as `"%(thiskey)s"`, and one can reference the
    *value* of all other keys in a report by name.

    As an example, consider the default `report_fmt="%(ins)s.%(pgm)s.%(thiskey)s"`.
    For a report from a `cmsd` daemon named `server`, the key `"ver"` is
    transformed to `"server.cmsd.ver"`.

    :see: https://docs.python.org/3/library/stdtypes.html#old-string-formatting
    """
    def __init__(self, report_fmt="%(ins)s.%(pgm)s.%(thiskey)s"):
        super(FormatTransform, self).__init__()
        self.report_fmt = report_fmt

    def send(self, report=None):
        """Rename and pass on a report"""
        if self.report_fmt != "%(thiskey)s":
            report_fmt = self.report_fmt
            report_map = report.copy()
            new_report = {}
            for key in report:
                report_map['thiskey'] = key
                new_report[report_fmt % report_map] = report[key]
            report = new_report
        super(FormatTransform, self).send(report)

    def _elem_repr(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(
            '%s=%r' % (key, getattr(self, key)) for key in ('report_fmt',)
        ))
