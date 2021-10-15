.. py:currentmodule:: lsst.ts.ess.controller

.. _lsst.ts.ess.controller.version_history:

###############
Version History
###############

v0.4.0
======

* Replaced the use of ts_salobj functions with ts_utils functions.
* Moved all device reply validating code to ts.ess.common.
* Moved all sensors code from ts.ess.controller to ts.ess.common.
* Moved code to determine what sensor is connected from ts.ess.controller to ts.ess.common.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.3.0
======

* Added support for the Omega HX85A and HX85BA humidity sensors.
* Made the FTDI and RpiSerialHat devices work.
* Added exception handling in the sensors code.
* Cleaned up the Python modules.
* Added dcoumentation for the sensor protocols.
* Validating incoming configurations against a JSON schema instead of using very complicated custom code.
* Renamed the project to ts_ess_controller and extracted common code to ts_ess_common.

Requires:

* ts_ess_common
* ts_tcpip 0.3.1


v0.2.0
======

* Made the conda package `noarch`.

Requires:

* ts_tcpip 0.3.1


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
