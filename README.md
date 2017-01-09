# XRootD Alice Monitor

Monitoring for XRootD servers for the MonALISA framework.
This tool collects data about a local XRootD server and sends it to a MonALISA host.
It is written primarily for XRootD servers used by the ALICE collaboration.

# About

This tool is based on Adrian's [alicexrd](https://github.com/adriansev/alicexrd) toolset,
aiming to separate responsibilities and simplify service management with Puppet.
Monitoring is the *only* ALICE-specific functionality that is not feasible to provide via service management tools.

At the moment, the repository is public for reference only.
If you just want to deploy an XRootD service for ALICE, *use Adrian's tools*.

# Dependencies

The current version relies on `servMon.sh` and `ApMon` being available.
Both are available from the `alicexrdplugins` metapackage, and can be installed via:

    rpm -Uvh http://linuxsoft.cern.ch/wlcg/sl6/x86_64/wlcg-repo-1.0.0-1.el6.noarch.rpm
    yum install alicexrdplugins
   