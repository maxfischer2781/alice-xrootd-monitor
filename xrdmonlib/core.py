from __future__ import division, absolute_import
import logging

from . import xrdreports


class Core(object):
    """
    Main report chain, collects reports and sends data via backends

    :param report_port: the port on which to listen for xrootd reports
    :type report_port: int
    :param backend_chain: chain of backends which process reports
    :type backend_chain: xrdmon.backend.base.ChainStart
    """
    def __init__(self, report_port, backend_chain):
        self.report_port = report_port
        self.backend_chain = backend_chain
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    def run(self):
        """
        The main loop, collecting reports and triggering backends
        """
        self._logger.info('starting xrdmon main loop')
        with xrdreports.XRootDReportStreamer(port=self.report_port) as report_stream:
            for report in report_stream:
                self.backend_chain.send(report)
        self._logger.info('stopping xrdmon main loop')
