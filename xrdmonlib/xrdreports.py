"""
Tools to interact with XRootD's `report` functionality
"""
from __future__ import division, absolute_import
import time
import logging
import subprocess

from . import utils


class XRootDReportStreamer(object):
    """
    Collects information generated by the `all.report` directive

    :param port: port receiving reports
    :type port: int

    A manager object provides reports as dictionaries on iteration. Reports
    are buffered asynchronously of iteration. Buffering is active after a call
    to :py:meth:`~.open`, and the buffer is cleared by a call to
    :py:meth:`~.close`. The buffer is also opened when iteration starts on an
    empty buffer.

    It is suggested to use this class as a context manager: the buffer is
    opened on entry and closed on exit of the context. This ensures the
    underlying resources are not unnecessarily blocked.

    :note: Reports are not buffered for multiple readers. If more than one
           thread reads reports, each receives only a fraction of reports.
    """
    def __init__(self, port):
        self.port = port
        self._reportstreamer = None
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    @property
    def streaming(self):
        """Whether streaming is in progress and message are read/buffered"""
        return self._reportstreamer is not None and self._reportstreamer.poll() is None

    def open(self):
        """Start collecting reports"""
        if self._reportstreamer is None:
            self._logger.info('opening report stream on port %d', self.port)
            self._reportstreamer = subprocess.Popen(
                ['mpxstats', '-p', str(self.port), '-f', 'cgi'],
                stdout=subprocess.PIPE
            )
            self._logger.info('buffering report stream')

    def close(self):
        """Stop collecting reports"""
        if self._reportstreamer is not None:
            if self._reportstreamer.poll() is None:
                self._reportstreamer.terminate()
                time.sleep(0.1)
            self._logger.info('closed report stream on port %d (exit code: %s)', self.port, self._reportstreamer.poll())
            self._reportstreamer = None

    def __iter__(self):
        self.open()
        datastream = self._reportstreamer.stdout
        self._logger.info('consuming report stream')
        try:
            for line in datastream:
                self._logger.debug('received datagram')
                datagram = dict(item.split('=') for item in line.split('&'))
                for key in datagram:
                    datagram[key] = utils.safe_eval(datagram[key])
                yield datagram
        finally:
            self._logger.info('releasing report stream')

    def __enter__(self):
        # start collection on entering the context, do not delay until consumption
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __del__(self):
        self.close()