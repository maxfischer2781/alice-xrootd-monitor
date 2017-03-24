from __future__ import division, absolute_import

import logging
import socket
import time

import apmon
import chainlet

from .. import utils
from ..utilities import dfs_counter


class ApMonLogger(object):
    """
    Replacement for ApMon `Logger.Logger` class to use default python logging

    :param defaultLevel: ignored, available for signature compatibility only

    Redirects ApMon logging calls messages using the standard :py:mod:`logging`
    utilities. This is intended for compatibility with backend code, mainly
    ApMon itself. If you wish to change ApMon logging settings, directly modify
    the logger `"xrdmonlib.ApMonLogger"`.
    """
    #: log levels as used by ApMon Logger
    apmon_levels = ('FATAL', 'ERROR', 'WARNING', 'INFO', 'NOTICE', 'DEBUG')
    #: map from apmon levels to logging levels
    level_map = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG,
        5: logging.DEBUG,
    }

    def __init__(self, defaultLevel=None):
        self._logger = logging.getLogger('%s.%s' % (__name__.split('.')[0], self.__class__.__name__))
        self._logger.warning('redirecting ApMon logging to native logger %r', self._logger.name)

    def log(self, level, message, printex=False):
        """Log a message from ApMon"""
        self._logger.log(self.level_map[level], '[ApMon] %s', message, exc_info=printex)

    def setLogLevel(self, strLevel):
        """Set the logging level"""
        logging_level = self.level_map[self.apmon_levels.index(strLevel)]
        self._logger.setLevel(logging_level)
        self._logger.log(logging_level, 'logging level set via ApMon: %s => %s', strLevel, logging_level)
for _level, _name in enumerate(ApMonLogger.apmon_levels):
    setattr(ApMonLogger, _name, _level)


class ApMonReport(dict):
    """
    Container for named reports for ApMon

    :param cluster_name: identifier for the host group this report applies to
    :type cluster_name: str
    :param node_name: identifier for the host this report applies to
    :type node_name: str
    :param params: parameters to send
    :type params: dict
    """
    def __int__(self, cluster_name, node_name, params):
        super(ApMonReport, self).__init__(self)
        self.cluster_name = cluster_name
        self.node_name = node_name
        self.update(params)


class ApMonConverter(chainlet.ChainLink):
    """
    BaseClass for Converters from report dicts to :py:class:`ApMonReport`
    """
    def __init__(self):
        super(ApMonConverter, self).__init__()
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._hostname = socket.getfqdn()

    def _xrootd_cluster_name(self, report):
        """Format report information to create ALICE cluster name"""
        return '%(se_name)s_%(instance)s_%(daemon)s_Services' % {
            'se_name': report['site'],  # must be defined via all.sitename
            'instance': report['ins'],
            'daemon': report['pgm'],
        }


class XrootdSpace(ApMonConverter):
    """
    Extract XRootD Space information from reports

    Provides key statistics on available space on an xrootd oss:

    *xrootd_version*
        The version of the xrootd daemon

    *space_total*
        The total space in MiB

    *space_free*
        The available space in MiB

    *space_largestfreechunk*
        The largest, consecutive available space in MiB
    """
    def __init__(self):
        super(XrootdSpace, self).__init__()
        self._space_counters = {}

    def send(self, value=None):
        space_count = value.get('oss.space')
        if 'oss.space' not in value:
            return self.stop_traversal
        space_share = self._get_space_share(value)
        xrootd_report = {
            'xrootd_version': value['ver'],
            # reports are in kiB, MonALISA expects MiB
            'space_total': sum(value['oss.space.%d.tot' % scount] for scount in range(space_count)) * space_share / 1024,
            'space_free': sum(value['oss.space.%d.free' % scount] for scount in range(space_count)) * space_share / 1024,
            'space_largestfreechunk': sum(value['oss.space.%d.maxf' % scount] for scount in range(space_count)) * space_share / 1024,
        }
        return ApMonReport(cluster_name=self._xrootd_cluster_name(value), node_name=self._hostname, params=xrootd_report)

    def _get_space_share(self, value):
        space_count = value['oss.space']
        # collect number of hosts concurrently serving from storage
        space_paths = set(value['oss.paths.%d.rp' % scount] for scount in range(space_count))
        for space_path in space_paths:
            if space_path not in self._space_counters:
                self._space_counters[space_path] = dfs_counter.DFSCounter(space_path)
        # clean up leftover paths
        for space_path in set(utils.viewkeys(self._space_counters)):
            if space_path not in space_paths:
                del self._space_counters[space_path]
        return sum(1/concurrency for concurrency in self._space_counters.values()) / len(self._space_counters)


class AliceApMonBackend(ApMonConverter):
    """
    Backend for ApMon client to MonALISA Monitoring

    :param destination: where to send data to, as `"hostname:port"`
    :type destination: str
    """
    def __init__(self, *destination):
        super(AliceApMonBackend, self).__init__()
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        # initialization
        self.destination = destination
        # initialize ApMon, reroute logging by replacing Logger at module level
        apmon_logger, apmon.Logger = apmon.Logger, ApMonLogger
        self._apmon = apmon.ApMon(destination)
        apmon.Logger = apmon_logger
        # background monitoring
        self._background_monitor_sitename = None
        self._service_job_monitor = set()

    def send(self, value=None):
        """Send reports via ApMon"""
        # preformatted report
        if self._send_apmon_report(value):
            return value
        # regular xrootd report
        self._monitor_host(value)
        self._monitor_service(value)

    def _send_apmon_report(self, value):
        """Send a report preprocessed for apmon"""
        if isinstance(value, ApMonReport):
            cluster_name = value.cluster_name
            node_name = value.node_name
            self._apmon.sendParameters(
                clusterName=cluster_name,
                nodeName=node_name,
                params=value
            )
            self._logger.info('apmon report for %r @ %r sent to %s' % (cluster_name, node_name, str(self.destination)))
            return True
        else:
            return False

    def _send_raw_report(self, value):
        """Send a raw report from xrootd"""
        self._send_apmon_report(ApMonReport(
            cluster_name='%(se_name)s_xrootd_ApMon_Info' % {'se_name': value['site']},
            node_name=self._hostname,
            params=value
        ))

    def _monitor_host(self, value):
        """Add background monitoring for this host"""
        try:
            se_name = value['site']
        except KeyError:
            return False
        if self._background_monitor_sitename == se_name:
            return
        # configure background monitoring
        cluster_name = '%(se_name)s_xrootd_SysInfo' % {'se_name': se_name}
        self._apmon.setMonitorClusterNode(
            cluster_name,
            self._hostname
        )
        self._apmon.enableBgMonitoring(True)
        self._background_monitor_sitename = se_name
        self._logger.info(
            'apmon host monitor for %r @ %r added to %s' % (cluster_name, self._hostname, str(self.destination))
        )
        return True

    def _monitor_service(self, report):
        """Add background monitoring for a service"""
        if 'pgm' not in report or 'pid' not in report:
            return
        pid, now = int(report['pid']), time.time()
        # add new services for monitoring
        if pid not in self._service_job_monitor:
            cluster_name = self._xrootd_cluster_name(report)
            self._apmon.addJobToMonitor(
                pid=pid,
                workDir='',
                clusterName=cluster_name,
                nodeName=self._hostname,
            )
            self._service_job_monitor.add(pid)
            self._logger.info(
                'apmon job monitor for %r @ %r added to %s' % (cluster_name, self._hostname, str(self.destination))
            )
        for pid in list(self._service_job_monitor):
            if not utils.validate_process(pid):
                self._apmon.removeJobToMonitor(pid)
                self._service_job_monitor.discard(pid)


#: full ALICE monitoring backend stack
def alice_apmon(*destinations):
    """
    Factory for ALICE ApMon Backend

    :param destination: where to send data to, as `"hostname:port"`
    :type destination: str
    """
    backend = AliceApMonBackend(*destinations)
    return chainlet.ChainLink() >> (XrootdSpace() >> backend, backend)
