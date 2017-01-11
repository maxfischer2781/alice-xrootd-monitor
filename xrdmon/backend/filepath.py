from __future__ import division, absolute_import
import time

from .. import targets


class FileBackend(object):
    """
    Backend writing to files
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self._data_servers = set()
        self._last_update = time.time()

    @staticmethod
    def _format_message(*keyvalues):
        return '\n'.join('%s=%s' % (key, value) for key, value in keyvalues) + '\n\n'

    def _write_data(self, *keyvalues):
        message = self._format_message(*keyvalues)
        with open(self.file_path, 'a') as output_file:
            output_file.write(message)
            output_file.flush()

    def digest_report(self, report):
        """Digest a report"""
        self._write_data(*sorted(report.items()))

    def insert_target(self, target):
        """Insert a new target for data extraction"""
        if isinstance(target, targets.XrdDaemonTarget):
            self._write_data(
                ('target', 'insert'),
                ('name', target.name),
                ('flavour', target.flavour),
                ('pid', target.pid),
                ('port', target.port),
            )
        if isinstance(target, targets.XRootDTarget):
            self._data_servers.add(target)

    def remove_target(self, target):
        """Remove an existing target from data extraction"""
        if isinstance(target, targets.XrdDaemonTarget):
            self._write_data(
                ('target', 'remove'),
                ('name', target.name),
                ('flavour', target.flavour),
                ('pid', target.pid),
                ('port', target.port),
            )
        if isinstance(target, targets.XRootDTarget):
            self._data_servers.discard(target)

    def update(self):
        """Run an update to get/commit information"""
        now = time.time()
        content = [('update', now - self._last_update)]
        for server in self._data_servers:
            content.append(('name', server.name))
            content.extend(
                (server.name + attr, getattr(server, attr)) for attr in (
                    'space_total', 'space_free', 'space_largestfreechunk'
                )
            )
        self._write_data(*content)
        self._last_update = now
