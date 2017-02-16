from __future__ import division, absolute_import

import chainlet


class FileBackend(chainlet.ChainLink):
    """
    Writes to files in plain `key=value` format

    :param file_path: absolute path to write message to
    :type file_path: str
    """
    def __init__(self, file_path):
        super(FileBackend, self).__init__()
        self.file_path = file_path

    @staticmethod
    def _format_message(*keyvalues):
        return '\n'.join('%s=%s' % (key, value) for key, value in keyvalues) + '\n\n'

    def _write_data(self, *keyvalues):
        message = self._format_message(*keyvalues)
        with open(self.file_path, 'a') as output_file:
            output_file.write(message)
            output_file.flush()

    def send(self, value=None):
        """
        Digest a report

        :param value: an xrootd report to digest
        :type value: dict
        """
        self._write_data(*sorted(value.items()))


class CGIFileBackend(FileBackend):
    """
    Writes to files in short, CGI format

    :param file_path: absolute path to write message to
    :type file_path: str
    """
    @staticmethod
    def _format_message(*keyvalues):
        return '&'.join('%s=%s' % (key, value) for key, value in keyvalues) + '\n'
