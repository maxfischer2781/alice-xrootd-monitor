from __future__ import division, absolute_import
import logging

from . import targets


class TargetProvider(object):
    """
    Baseclass for providers of monitoring targets from a report stream

    :param report_stream: stream of reports to inspect

    Target providers inspect a report stream, creating potential targets for
    further monitoring. The stream is passed on via iteration over the
    :py:class:`~TargetProvider` inspecting it: elements in `iter(stream)` and
    `iter(TargetProvider(stream))` are the same.

    In addition, each provider exposes possible targets via its attribute
    :py:attr:`targets`.
    """
    def __init__(self, report_stream, on_insert=None, on_remove=None):
        self.report_stream = report_stream
        self._on_remove = on_remove
        self._on_insert = on_insert
        self.targets = set()
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    def __iter__(self):
        for report in self.report_stream:
            self._inspect_report(report)
            yield report

    def _insert_target(self, target):
        self.targets.add(target)
        if self._on_insert:
            self._on_insert(target)

    def _remove_target(self, target):
        self.targets.discard(target)
        if self._on_remove:
            self._on_remove(target)

    def _inspect_report(self, report):
        pass


class XRootDTargetProvider(TargetProvider):
    """
    Provider for XRootD daemons as monitoring targets
    """
    def _inspect_report(self, report):
        if 'pgm' in report:
            new_target = targets.XrdDaemonTarget.from_report(report)
            self._insert_target(new_target)
            self._logger.info('insert target: %s', new_target)
        for target in self.targets:
            if not target.alive:
                self._remove_target(target)
                self._logger.info('remove target: %s', target)
