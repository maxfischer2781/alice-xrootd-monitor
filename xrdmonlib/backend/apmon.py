from __future__ import division, absolute_import

import logging
import socket

import apmon
import chainlet

from .. import compat


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


class AliceApMonBackend(chainlet.ChainLink):
    """
    Backend for ApMon client to MonALISA Monitoring

    Data is formatted according to conventions of the ALICE collaboration.

    :param host_group: name of the cluster this node belongs to (SE name)
    :type host_group: str
    :param destination: where to send data to, as `"hostname:port"`
    :type destination: str
    :param scale_space: factor to scale storage space reports, on top of unit conversions
    :type scale_space: int or float
    """
    def __init__(self, host_group, destination, scale_space=1):
        super(AliceApMonBackend, self).__init__()
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        # configuration checks
        self._validate_parameters(host_group, destination)
        # initialization
        self.destination = destination
        self.host_group = host_group
        self.scale_space = scale_space
        self._hostname = socket.getfqdn()
        # initialize ApMon, reroute logging
        apmon_logger, apmon.Logger = apmon.Logger, ApMonLogger
        self._apmon = apmon.ApMon((destination,))
        apmon.Logger = apmon_logger
        # start monitoring
        self._apmon.enableBgMonitoring(True)

    def _validate_parameters(self, host_group, destination):
        """validate parameters for cleaner configuration"""
        if not isinstance(host_group, compat.string_type):
            raise TypeError("%s: 'host_group' must be a string, got %r (%s)" % (
                self.__class__.__name__, host_group, type(host_group).__name__
            ))
        if not isinstance(destination, compat.string_type):
            raise TypeError("%s: 'destination' must be a string, got %r (%s)" % (
                self.__class__.__name__, destination, type(destination).__name__
            ))

    def send(self, value=None):
        """Send reports via ApMon"""
        self._apmon.sendBgMonitoring()
        if value['pgm'] == 'xrootd':
            self._report_xrootd_space(value)
        self._apmon.sendParameters(
            clusterName='%(se_name)s_ApMon_Info' % {'se_name': self.host_group},
            nodeName=self._hostname,
            params=value
        )

    def _report_xrootd_space(self, report):
        """Send report for xrootd daemon space"""
        space_count = report.get('oss.space')
        if space_count is None:
            self._logger.warning("missing key group 'oss.space.*' in report, skipping storage space report")
            return
        xrootd_report = {
            'xrootd_version': report['ver'],
            # reports are in kiB, MonALISA expects MiB
            'space_total': sum(report['oss.space.%d.tot' % scount] for scount in range(space_count)) / self.scale_space / 1024,
            'space_free': sum(report['oss.space.%d.free' % scount] for scount in range(space_count)) / self.scale_space / 1024,
            'space_largestfreechunk': sum(report['oss.space.%d.maxf' % scount] for scount in range(space_count)) / self.scale_space / 1024,
        }
        self._apmon.sendParameters(
            clusterName=self._xrootd_cluster_name(report),
            nodeName=self._hostname,
            params=xrootd_report,
        )

    def _xrootd_cluster_name(self, report):
        """Format report information to create ALICE cluster name"""
        return '%(se_name)s_%(name)s_%(flavour)s_Services' % {
            'se_name': self.host_group,
            'name': report['ins'],
            'flavour': report['pgm'],
        }
