.. py:currentmodule:: lsst.ts.envsensors

.. _lsst.ts.envsensors:

##################
lsst.ts.envsensors
##################

SocketServer and sensor reading code for the Environmental Sensors Support system at Vera C. Rubin Observatory.
The SocketServer is used to facilitate basic TCP/IP communication.
This communication will allow for starting and stopping the sensor reading code, as well as for configuring which sensors to read.
The sensor reading code will then send the sensor telemetry data back via the SocketServer.

.. .. _lsst.ts.envsensors-using:

.. Using lsst.ts.envsensors
.. =========================

.. toctree linking to topics related to using the module's APIs.

.. .. toctree::
..    :maxdepth: 1

.. _lsst.ts.envsensors-contributing:

Contributing
============

``lsst.ts.envsensors`` is developed at https://github.com/lsst-ts/ts_envsensors.
You can find Jira issues for this module using `labels=ts_envsensors <https://jira.lsstcorp.org/issues/?jql=project%3DDM%20AND%20labels%3Dts_envsensors>`_.

Python API reference
====================

.. automodapi:: lsst.ts.envsensors
   :no-main-docstr:

Version History
===============

.. toctree::
    version_history
    :maxdepth: 1
