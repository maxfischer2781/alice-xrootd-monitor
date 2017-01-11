"""
Representation of processes to be monitored
"""
from __future__ import absolute_import, division
import subprocess
import time

from . import utils


class XrdDaemonTarget(object):
    """
    Baseclass for daemons of XRootD
    """
    flavour = "none"

    def __init__(self, name, version, pid, port=None):
        self.name = name
        self.pid = pid
        self.port = port
        self.version = version
        self._identity = self._get_identity()
        self._hash = hash(self._identity)

    @property
    def alive(self):
        """Whether the daemon is running"""
        return utils.validate_process(pid=self.pid, name=self.flavour)

    @classmethod
    def from_report(cls, report):
        """Instantiate (child) class from xrootd report"""
        if "pgm" not in report:
            raise ValueError('report without "pgm" identifier for flavour')
        for scls in cls.__subclasses__():
            if scls.flavour == report["pgm"]:
                if scls.from_report is cls.from_report:
                    return scls(
                        name=report["ins"],
                        version=report["ver"],
                        pid=report["pid"],
                        port=report.get('info.port', 0)
                    )
                return scls.from_report(report)
        raise ValueError('unknown "pgm" flavour: %r' % report["pgm"])

    def _get_identity(self):
        return self.__class__, self.flavour, self.name, self.pid, self.port

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if isinstance(other, XrdDaemonTarget):
            return self._identity == other._identity
        return NotImplemented


class CmsdTarget(XrdDaemonTarget):
    """cmsd process"""
    flavour = "cmsd"


class XRootDTarget(XrdDaemonTarget):
    """xrootd process"""
    flavour = "xrootd"

    def __init__(self, *args, **kwargs):
        #: time and content of last server query
        self._last_query = (0, {})
        super(XRootDTarget, self).__init__(*args, **kwargs)

    @property
    def space_total(self):
        self._ensure_query()
        return self._last_query[1].get('Total', 0)

    @property
    def space_free(self):
        self._ensure_query()
        return self._last_query[1].get('Free', 0)

    @property
    def space_largestfreechunk(self):
        self._ensure_query()
        return self._last_query[1].get('Largest free chunk', 0)

    def _ensure_query(self):
        if time.time() - self._last_query[0] > 5*60:
            self._query_space()

    def _query_space(self):
        xrdfs_proc = subprocess.Popen(["xrdfs", "localhost:%s" % self.port], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        xrdfs_proc.stdin.write('spaceinfo /\nexit\n')
        query_info = {}
        for line in xrdfs_proc.stdout:
            # ignore command line prompt
            if line[:11] == '[localhost:':
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = utils.safe_eval(value.strip())
                query_info[key] = value
        self._last_query = (time.time(), query_info)
