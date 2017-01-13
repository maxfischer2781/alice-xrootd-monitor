from __future__ import division, absolute_import
import socket

import apmon

from .. import targets
from .. import compat


class AliceApMonBackend(object):
    """
    Backend for ApMon client to MonALISA Monitoring

    Data is formatted according to conventions of the ALICE collaboration.

    :param host_group: name of the cluster this node belongs to
    :type host_group: str
    :param destinations: where to send data to, as `"hostname:port"`
    :type destinations: tuple[str]
    """
    def __init__(self, host_group, destinations=()):
        # configuration checks
        destinations = (destinations,) if isinstance(destinations, compat.string_type) else tuple(destinations)
        self._validate_parameters(host_group, destinations)
        # initialization
        self.destinations = tuple(destinations)
        self.host_group = host_group
        self._apmon = apmon.ApMon(destinations)
        self._apmon.enableBgMonitoring(True)
        self._hostname = socket.getfqdn()
        self._data_servers = set()

    def _validate_parameters(self, host_group, destinations):
        """validate parameters for cleaner configuration"""
        if not isinstance(host_group, compat.string_type):
            raise TypeError("%s: 'host_group' must be a string, got %r (%s)" % (
                self.__class__.__name__, host_group, type(host_group).__name__
            ))
        for destination in destinations:
            if not isinstance(destination, compat.string_type):
                raise TypeError("%s: 'destinations' must be a sequence of strings, got %r (%s)" % (
                    self.__class__.__name__,host_group, type(host_group).__name__
                ))

    def _xrootd_cluster_name(self, daemon):
        return '%(se_name)s_%(name)s_%(flavour)s_Services' % {
            'se_name': self.host_group,
            'name': daemon.name,
            'flavour': daemon.flavour,
        }

    def digest_report(self, report):
        """Digest a report"""
        pass

    def insert_target(self, target):
        """Insert a new target for data extraction"""
        if isinstance(target, targets.XrdDaemonTarget) and target.pid not in self._apmon.monitoredJobs:
            self._apmon.addJobToMonitor(
                pid=target.pid,
                workDir='',
                clusterName=self._xrootd_cluster_name(target),
                nodeName=self._hostname,
            )
        if isinstance(target, targets.XRootDTarget):
            self._data_servers.add(target)

    def remove_target(self, target):
        """Remove an existing target from data extraction"""
        if isinstance(target, targets.XrdDaemonTarget) and target.pid in self._apmon.monitoredJobs:
            self._apmon.removeJobToMonitor(target.pid)
        if isinstance(target, targets.XRootDTarget):
            self._data_servers.discard(target)

    def update(self):
        """Run an update to get/commit information"""
        self._apmon.sendBgMonitoring()
        for server in self._data_servers:
            cluster_name = self._xrootd_cluster_name(server)
            server_stats = {
                'xrootd_version': server.version,
                'space_total': server.space_total,
                'space_free': server.space_free,
                'space_largestfreechunk': server.space_largestfreechunk,
            }
            self._apmon.sendParameters(
                clusterName=cluster_name,
                nodeName=self._hostname,
                params=server_stats
            )

