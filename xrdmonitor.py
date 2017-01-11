import argparse
import os

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

if __name__ == '__main__':
    options = CLI.parse_args()
    main = core.Core(
        report_port=options.report_port,
        backends=[filepath.FileBackend(file_path=options.file_path)]
    )
