# XRootD Monitor

Monitoring suite for XRootD servers.
This tool collects, transforms and generates data about a local XRootD server.
Multiple backends are available to pass on this data.

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
