Configuration
#############

When using ``xrdmonlib`` via ``xrdmon``, the service is configured using the convention of :py:mod:`xrdmonlib.interface`.
The single required argument to  ``xrdmon`` is the path to a configuration file.

A simple example is below.
It sets the port to listen for xrootd reports and redirects them to a log file.

.. code:: python

    core << Reports(10333)
    core >> LogFile("/tmp/xrdmon.log")

Redirection Chains
==================

Processing of reports is based on redirecting the report stream through a chain.
Each element can inspect, transform and digest reports.

Elements are connected using the ``>>`` operator.
The report stream flows in only one direction:
given the link ``source >> consumer``, changes made by ``source`` are visible to ``consumer`` but *not* vice versa.

A common use case is to remove unneeded elements from reports.
The following example removes all keys starting with ``"buff"`` from reports before they are written to disk.

.. code:: python

    core >> Filter(r"^buff\..*") >> LogFile("/tmp/xrdmon.log")

Forking Streams
---------------

A major use case for report stream redirection in ``xrdmonlib`` is forking.
At each element of a report chain, the stream can be forked to multiple children.

The simplest way to fork a stream is to redirect it directly to multiple consumers.
This is expressed by redirection to a ``tuple`` of consumers.

.. code:: python

    core >> (LogFile("/tmp/xrdmon.log"), CGIFile("/tmp/xrdmon.cgi"))

Note that a consumer can be yet another chain.
For example, this can be used to apply filters to only some output.

.. code:: python

    core >> (LogFile("/tmp/xrdmon.log"), Filter(r"^buff\..*") >> LogFile("/tmp/xrdmon_short.log"))

Alternatively, you can redirect from one element multiple times.
The following example gives the same result as the previous one.

.. code:: python

    core >> LogFile("/tmp/xrdmon.log")
    core >> Filter(r"^buff\..*") >> LogFile("/tmp/xrdmon_short.log"))

Default Elements
----------------

A number of report chain elements are available by default.
These map to Python classes, which define their parameters.

.. autogenerate these?

Configuration File Syntax and Capabilities
==========================================

The configuration file is actually a valid Python file and executed as such.
You can make use of the full Python syntax, including comments and scoping.

.. code:: python

    core >> (
        # verbose log
        LogFile("/tmp/xrdmon.log"),
        # long running, filtered log
        Filter(r"^buff\..*") >> LogFile("/tmp/xrdmon_short.log")
    )

:warning: The configuration file is executed with all permissions of the current user.
          You should ensure that it is *not writeable* to any untrusted users.

Logging Setup
-------------

All debug logging by ``xrdmonlib`` uses the default :py:mod:`logging` module.
To change logging, simply import the module and configure it to your needs.

.. code:: python

    import logging.handlers
    logging.getLogger('xrdmonlib').addHandler(logging.handlers.SysLogHandler())

See the :py:mod:`logging` documentation for possible options
(`Python2 <https://docs.python.org/2/library/logging.html>`_ and `Python3 <https://docs.python.org/3/library/logging.html>`_).

Custom Chain Elements
---------------------

As the configuration is Python, one can easily plug in extensions if needed.
Elements of the report chain are implemented using :py:mod:`chainlet`.
Each simply receives a ``dict`` via their :py:meth:`send` method.

.. code:: python

    import time
    from chainlet import ChainLink

    # custom chain element
    class Timestamper(ChainLink):
        def send(self, value=None):
            """
            Digest a report, adding a timestamp

            :param value: an xrootd report to digest
            :type value: dict
            """
            report['tme'] = time.time()
            super(TimestampElement, self).send(report)

    core >> Timestamper() >> LogFile("/tmp/xrdmon_short.log"))
