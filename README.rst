#################
ts_ess_controller
#################

``ts_ess_controller`` is a package in the `LSST Science Pipelines <https://pipelines.lsst.io>`_.

SocketServer and sensor reading code for the Environmental Sensors Support system at Vera C. Rubin Observatory.
The SocketServer is used to facilitate basic TCP/IP communication.
This communication will allow for starting and stopping the sensor reading code, as well as for configuring which sensors to read.
The sensor reading code will then send the sensor telemetry data back via the SocketServer.

Both FTDI and Serial connections of the sensors are supported.
It is unlikely that more connection types will be added in the future.

Currently the following sensor types are supported:

    - Custom RTD and Thermal Couple temperature sensors
    - Omage HX85A and HX85BA humidity sensors
    - Gil WindSonic 2D wind sensors
