from __future__ import division, absolute_import
import logging

from . import xrdreports


class Core(object):
    """
    Main report chain, collects reports and sends data via backends

    :param report_port: the port on which to listen for xrootd reports
    :type report_port: int
    :param backends: backends which processing reports
    :type backends: xrdmon.backend.base.ChainStart
    """
    def __init__(self, report_port, backends=None):
        self.report_port = report_port
        self.backends = backends if backends is not None else []
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    def run(self):
        """
        The main loop, collecting reports and triggering backends
        """
        self._logger.info('starting xrdmon main loop')
        with xrdreports.XRootDReportStreamer(port=self.report_port) as report_stream:
            for report in report_stream:
                for backend in self.backends:
                    backend.send(report)
        self._logger.info('stopping xrdmon main loop')
