Configuration
#############

When using `xrdmonlib` via `xrdmon`, the service is configured using the convention of :py:mod:`xrdmonlib.interface`.
The single required argument to  `xrdmon` is the path to a configuration file.

A simple example is below.
It sets the port to listen for xrootd reports and redirects them to a log file.

.. code:: python

    port = 12345
    reports >> LogFile("/tmp/xrdmon.log")

Redirection Chains
==================

Processing of reports is based on redirecting the report stream through a chain.
Each element can inspect, transform and digest reports.

Elements are connected using the `>>` operator.
The report stream flows in only one direction:
given the link `source >> consumer`, changes made by `source` are visible to `consumer` but *not* vice versa.

A common use case is to remove unneeded elements from reports.
The following example removes all keys starting with `"buff"` from reports before they are written to disk.

.. code:: python

    reports >> Filter(r"^buff\..*") >> LogFile("/tmp/xrdmon.log")

Forking Streams
===============

A major use case for report stream redirection in `xrdmonlib` is forking.
At each element of a report chain, the stream can be forked to multiple children.

The simplest way to fork a stream is to redirect it directly to multiple consumers.
This is expressed by redirection to a `tuple` of consumers.

.. code:: python

    reports >> (LogFile("/tmp/xrdmon.log"), CGIFile("/tmp/xrdmon.cgi"))

Note that a consumer can be yet another chain.
This can be used to apply filters to some output.

    reports >> (LogFile("/tmp/xrdmon.log"), Filter(r"^buff\..*") >> LogFile("/tmp/xrdmon_short.log"))

Alternatively, you can redirect from one element multiple times.
The following example gives the same result as the previous one.

.. code:: python

    reports >> LogFile("/tmp/xrdmon.log")
    reports >> Filter(r"^buff\..*") >> LogFile("/tmp/xrdmon_short.log"))

.. note::
   While streams can be forked, they *cannot be joined* at the moment.

Default Elements
================

A number of report chain elements are available by default.
These map to Python classes, which define their parameters.

.. autogenerate these?

Configuration File Syntax and Capabilities
------------------------------------------

The configuration file is actually a valid Python file and executed as such.
You can make use of the full Python syntax, including comments and scoping.

.. code:: python

    reports >> (
        # verbose log
        LogFile("/tmp/xrdmon.log"),
        # long running, filtered log
        Filter(r"^buff\..*") >> LogFile("/tmp/xrdmon_short.log")
    )

Furthermore, this allows to easily plug in extensions if needed.

.. warning::
   The configuration file is executed with all permissions of the current user.
   You should ensure that it is *not writeable* to any untrusted users.
