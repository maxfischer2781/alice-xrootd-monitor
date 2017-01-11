from __future__ import division, absolute_import
import time
import logging

from . import xrdreports
from . import targetprovider


class Core(object):
    """
    Main data chain, collecting reports and managing backends

    :param report_port: the port on which to listen for xrootd reports
    :type report_port: int
    :param backends: backends which process reports and other information
    :type backends: list[xrdmon.backend.filepath.FileBackend]
    """
    def __init__(self, report_port, backends=None, update_interval=60):
        self.report_port = report_port
        self.update_interval = update_interval
        self._last_update = time.time() - self.update_interval
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
                update_delta = time.time() - self._last_update
                if update_delta > self.update_interval:
                    for backend in self.backends:
                        backend.update(delta=update_delta)
                    self._last_update += (update_delta // self.update_interval) * self.update_interval

    def remove_target_callback(self, target):
        """Callback for target removal, forwarding to backends"""
        for backend in self.backends:
            backend.remove_target(target)

    def insert_target_callback(self, target):
        """Callback for target insertion, forwarding to backends"""
        for backend in self.backends:
            backend.insert_target(target)