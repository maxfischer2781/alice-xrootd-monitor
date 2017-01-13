from __future__ import division, absolute_import
import time
import logging

from . import xrdreports
from . import targetprovider


class Core(object):
    """
    Collects reports, identifies monitoring targets, and sends data via backends

    :param report_port: the port on which to listen for xrootd reports
    :type report_port: int
    :param update_interval: how long to wait between updates in seconds
    :type update_interval: float or int
    :param backends: backends which process reports and other information
    :type backends: list[xrdmon.backend.filepath.FileBackend]
    """
    def __init__(self, report_port, update_interval=60, backends=None):
        self.report_port = report_port
        self.update_interval = update_interval
        self._next_update = time.time()
        self.backends = backends if backends is not None else []
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    def run(self):
        """
        The main loop, collecting reports and triggering backends
        """
        with xrdreports.XRootDReportManager(port=self.report_port) as report_stream:
            report_stream = targetprovider.XRootDTargetProvider(
                report_stream,
                on_insert=self.insert_target_callback,
                on_remove=self.remove_target_callback,
            )
            for report in report_stream:
                for backend in self.backends:
                    backend.digest_report(report)
                if time.time() > self._next_update:
                    self._logger.info('running update: %s', time.time())
                    for backend in self.backends:
                        backend.update()
                    self._next_update += \
                        ((time.time() - self._next_update // self.update_interval) + 1) * self.update_interval

    def remove_target_callback(self, target):
        """Callback for target removal, forwarding to backends"""
        for backend in self.backends:
            backend.remove_target(target)

    def insert_target_callback(self, target):
        """Callback for target insertion, forwarding to backends"""
        for backend in self.backends:
            backend.insert_target(target)