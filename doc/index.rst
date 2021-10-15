.. py:currentmodule:: lsst.ts.ess.controller

.. _lsst.ts.ess.controller:

######################
lsst.ts.ess.controller
######################

SocketServer and sensor reading code for the Environmental Sensors Support system at Vera C. Rubin Observatory.
The SocketServer is used to facilitate basic TCP/IP communication.
This communication will allow for starting and stopping the sensor reading code, as well as for configuring which sensors to read.
The sensor reading code will then send the sensor telemetry data back via the SocketServer.
Note that the base device and all sensor code actually is in ts.ess.common.
This package only holds the code for the Raspberry P Serial Hat and VCP FTDI devices.

.. .. _lsst.ts.ess.controller-using:

Using lsst.ts.ess.controller
============================

The following sensors are supported:

.. toctree::
   gil_windsonic_2-d_sonic_wind_sensor
   omega_hx85a_sensor
   omega_hx85ba_sensor
   sel_temperature_sensor
   :maxdepth: 1

.. _lsst.ts.ess.controller-contributing:

Contributing
============

``lsst.ts.ess.controller`` is developed at https://github.com/lsst-ts/ts_ess_controller.
You can find Jira issues for this module using `labels=ts_ess_controller <https://jira.lsstcorp.org/issues/?jql=project%3DDM%20AND%20labels%3Dts_ess_controller>`_.

Python API reference
====================

.. automodapi:: lsst.ts.ess.controller
   :no-main-docstr:

Version History
===============

.. toctree::
    version_history
    :maxdepth: 1
