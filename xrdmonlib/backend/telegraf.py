from __future__ import absolute_import, division
import sys
import time

import chainlet

from .. import utils


def line_format(name, tags, fields, timestamp=None):
    """
    Format a report as InfluxDB line format

    :param name: name of the report
    :type name: str
    :param tags: tags identifying the specific report
    :type tags: dict[str]
    :param fields: measurements of the report
    :type fields: dict[str]
    :param timestamp: when the measurement was taken, in **seconds** since the epoch
    :type timestamp: float, int or None
    """
    output_str = name
    if tags:
        output_str += ',' + ','.join('%s=%s' % (key, value) for key, value in sorted(tags.items()))
    output_str += ' '
    output_str += ','.join(('%s=%r' % (key, value)).replace("'", '"') for key, value in sorted(fields.items()))
    if timestamp is not None:
        # line protocol requires nanosecond precision, python uses seconds
        output_str += ' %d' % (timestamp * 1E9)
    return output_str + '\n'


@chainlet.genlet
def telegraf_socket(address, name=sys.executable, tag_sets=None, tag_keys=(), fields=None, socket_type='UDP', time_resolution=1):
    """
    Send data to a telegraf socket listener

    :param address: the address to send data to, such as `('localhost', 8565)`
    :param name: name of the measurement
    :param tag_sets: fixed tags used to identify the measurement, e.g. `{'location': 'hawaii'}`
    :param tag_keys: keys to read from each report and add as tags
    :param fields: keys of the report to pass on as fields; if :py:const:`None`, pass on all non-tag keys
    :param socket_type: type of the connection, see below for types and address formats
    :type socket_type: str
    :param time_resolution: resolution at which timestamps are reported, in seconds


    **UDP**
        UDP datagrams via IPv4. Address is a tuple `(host:str, port:int)`, where `host` is an IPv4 or hostname.

    **TCP**
        TCP streaming via IPv4. Address is a tuple `(host:str, port:int)`, where `host` is an IPv4 or hostname.

    **UDP6**
        UDP datagrams via IPv6. Address is a tuple `(host:str, port:int)`, where `host` is an IPv6 or hostname.
        Alternatively, address may be a tuple `(host, port, flowinfo, scopeid)`.

    **TCP6**
        TCP streaming via IPv6. Address is a tuple `(host:str, port:int)`, where `host` is an IPv6 or hostname.
        Alternatively, address may be a tuple `(host, port, flowinfo, scopeid)`.

    **UNIXGRAM**
        Unix datagrams. Address is a string `path` of a named socket in the filesystem, or a bytes `name` of a socket
        in the abstract Linux namespace.

    **UNIX**
        Unix streaming. Address is a string `path` of a named socket in the filesystem, or a bytes `name` of a socket
        in the abstract Linux namespace.
    """
    tag_sets = tag_sets or {}
    _sock = utils.simple_socket(flavour=socket_type)
    report = yield
    while True:
        _tags = tag_sets.copy()
        _fields = {}
        for key in report:
            if key in tag_keys:
                _tags[key] = report[key]
            elif fields is None or key in fields:
                _fields[key] = report[key]
        message = line_format(
                name=name % report,
                tags=_tags,
                fields=_fields,
                timestamp=(time.time() // time_resolution)*time_resolution
            )
        while message:
            message = message[_sock.sendto(message, address):]
        report = yield
