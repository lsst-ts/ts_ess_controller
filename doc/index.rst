.. py:currentmodule:: lsst.ts.ess.controller

.. _lsst.ts.ess.controller:

######################
lsst.ts.ess.controller
######################

A "relay data server" that runs on Raspberry Pi controllers.
This serves sensor data in a way that the ESS RPiDataServer can read it.

SocketServer and sensor reading code for the Environmental Sensors Support system at Vera C. Rubin Observatory.
The SocketServer is used to facilitate basic TCP/IP communication.
This communication will allow for starting and stopping the sensor reading code, as well as for configuring which sensors to read.
The sensor reading code will then send the sensor telemetry data back via the SocketServer.
Note that the base device and all sensor code is in ts.ess.common.
This package only holds the code for the Raspberry Pi Serial Hat and VCP FTDI (Virtual COM Port Future Technology Device International) devices.

Note that for the Raspberry Pi Serial Hat devices, the GPIO pins need to be set to specific states at boot time.
This can be achieved by adding these lines to /boot/config.txt of the Raspberry Pi::

    # Set these pins to be an output
    gpio=11,17,18,23=op,dh

    # Set these pins to be an input
    gpio=7,24=ip

    # Set this pin to be an output as well
    gpio=3=op

Note that this is done automatically by Puppet for those Raspberry Pi devices that are provisioned that way.

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
