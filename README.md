# XRootD Monitor

Monitoring suite for XRootD servers.
This tool collects, transforms and generates report data about XRootD server.
Multiple backends are available to pass on this data.

# Quick Guide

The `xrdmon` expects xrootd to send monitoring reports to a fixed, local port.
These reports are multiplexed and can be sent to various consumers.
To start the monitor, simply run it with a configuration file path:

    xrdmon /path/to/config.cfg

A standard configuration file must specify the `port` to listen on, and redirect the `reports` to consumers.

    port = 20333
    reports >> LogFile("/tmp/xrdmon.log")
    reports >> AliceMon('ALICE::EXAMPLE::SE', 'localhost:8560')

# About

At the moment, the repository is public for reference only.
It is under development and testing at FZK.

This suite was initially written for XRootD servers of the ALICE collaboration.
Monitoring is the *only* ALICE-specific functionality that is not feasible to provide via service management tools.
If you just want to deploy an XRootD service for ALICE, use [Adrian's alicexrd tools](https://github.com/adriansev/alicexrd).

# Installation

The suite can be installed using standard Python package manager `pip` or from source.

Simply run

    pip install xrdmon

or check out this repository and run

    python setup.py install

# Notice

    This packages includes a backport of the runpy python module (http://www.python.org)
    Copyright (C) 2001-2016 Python Software Foundation.
    Licensed under the Python Software Foundation License.