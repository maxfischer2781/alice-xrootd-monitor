from __future__ import division, absolute_import
import logging

import chainlet.driver


class Core(chainlet.driver.ThreadedChainDriver):
    """
    Main report chain, collects reports and sends data via backends
    """
    def __init__(self):
        super(Core, self).__init__()
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    def run(self):
        """
        Collect and pass on reports
        """
        if not self.mounts:
            raise RuntimeError('No chains to process. Did you forget to call `core.mount(chain)`?')
        self._logger.info('Streaming reports from %d source(s)', len(self.mounts))
        self._logger.info('starting %s main loop', self.__class__.__name__)
        super(Core, self).run()
        self._logger.info('stopping %s main loop', self.__class__.__name__)
