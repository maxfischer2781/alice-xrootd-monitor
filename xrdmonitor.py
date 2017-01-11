from __future__ import division, absolute_import, print_function
import argparse
import os
import logging

from xrdmon import core
from xrdmon.backend import filepath

CLI = argparse.ArgumentParser('XRootD Monitor')
CLI.add_argument(
    '--report-port',
    help='port to listen for XRootD reports',
    type=int,
)
CLI.add_argument(
    '--file-path',
    help='path to write logs to',
    default='/tmp/%s.log' % (os.path.splitext(os.path.basename(__file__))[0])
)
CLI.add_argument(
    '--log-level',
    help='Log level to use',
    default='WARNING'
)

if __name__ == '__main__':
    options = CLI.parse_args()
    logging.basicConfig()
    log_level = options.log_level
    try:
        log_level = int(log_level)
    except ValueError:
        log_level = getattr(logging, log_level.upper())
    APP_LOGGER = logging.getLogger(os.path.basename('xrdmon'))
    APP_LOGGER.setLevel(log_level)
    APP_LOGGER.info('report_port=%s, file_path=%s', options.report_port, options.file_path)
    main = core.Core(
        report_port=options.report_port,
        backends=[filepath.FileBackend(file_path=options.file_path)]
    )
    main.run()
