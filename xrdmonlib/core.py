from __future__ import division, absolute_import
import logging

import chainlet.driver


class Core(chainlet.driver.ThreadedChainDriver):
    def __init__(self):
        super(Core, self).__init__()
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    def run(self):
        self._logger.info('Streaming reports from %d source(s) to %d chain(s)', len(self._parents), len(self._children))
        self._logger.info('starting %s main loop', self.__class__.__name__)
        super(Core, self).run()
        self._logger.info('stopping %s main loop', self.__class__.__name__)
