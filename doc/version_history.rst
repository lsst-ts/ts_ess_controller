.. py:currentmodule:: lsst.ts.envsensors

.. _lsst.ts.envsensors.version_history:

###############
Version History
###############

v0.1.0
======

First release of the Environmental Sensors Suite socket server and sensor reading code.

This version already includes many useful things:

* A functioning socket server (for which the ``ts_tcpip`` socket server is used).
* Code that reads the output of the connected sensors and sends the data via the socket server.
* Support for USB and FTDI sensors.
* Added support for connecting to and reading telemetry from multiple sensors.
* Added configuration error handling.

Requires:

* ts_tcpip 0.2.0
