# This file is part of ts_ess_controller.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ["CommandHandler"]

import typing

from .device import RpiSerialHat, VcpFtdi
from lsst.ts.ess import common


class CommandHandler(common.AbstractCommandHandler):
    """Handle incoming commands and send replies. Apply configuration and read
    sensor data.

    Parameters
    ----------
    callback : `Callable`
        The callback coroutine handling the sensor telemetry. This can be a
        coroutine that sends the data via a socket connection or a coroutine in
        a test class to verify that the command has been handled correctly.
    simulation_mode : `int`
        Indicating if a simulation mode (> 0) or not (0) is active.

    The commands that can be handled are:

        configure: Load the configuration that is passed on with the command
        and connect to the devices specified in that configuration. This
        command can be sent multiple times before a start is received and only
        the last configuration is kept.
        start: Start reading the sensor data of the connected devices and send
        it as plain text via the socket. If no configuration was sent then the
        start command is ignored. Once started no configuration changes can be
        done anymore.
        stop: Stop sending sensor data and disconnect from all devices. Once
        stopped, configuration changes can be done again and/or reading of
        sensor data can be started again.

    """

    valid_simulation_modes = (0, 1)

    def __init__(self, callback: typing.Callable, simulation_mode: int) -> None:
        super().__init__(callback=callback, simulation_mode=simulation_mode)

    def create_device(
        self, device_configuration: typing.Dict[str, typing.Any]
    ) -> common.device.BaseDevice:
        """Get the device to connect to by using the specified configuration.

        Parameters
        ----------
        device_configuration : `dict`
            A dict representing the device to connect to. The format of the
            dict follows the configuration of the ts_ess_csc project.

        Returns
        -------
        device : `common.device.BaseDevice`
            The device to connect to.

        Raises
        ------
        RuntimeError
            In case an incorrect configuration has been loaded.

        Notes
        -----
        In case simulation_mode is set to 1, only the sensor type is
        used and a mock device is instantiated.
        In case a serial device is specified, the device will only be
        instantiated if the code is running on a Raspberry Pi.
        In all other cases, the architecture of the platform is
        irrelevant.
        """
        sensor = common.sensor.create_sensor(
            device_configuration=device_configuration, log=self.log
        )
        if self.simulation_mode == 1:
            self.log.debug(
                f"Creating MockDevice with name {device_configuration[common.Key.NAME]} and sensor {sensor}"
            )
            device: common.device.BaseDevice = common.device.MockDevice(
                name=device_configuration[common.Key.NAME],
                device_id=device_configuration[common.Key.FTDI_ID],
                sensor=sensor,
                callback_func=self._callback,
                log=self.log,
            )
            return device
        elif device_configuration[common.Key.DEVICE_TYPE] == common.DeviceType.FTDI:
            self.log.debug(
                f"Creating VcpFtdi device with name {device_configuration[common.Key.NAME]} "
                f"and sensor {sensor}"
            )
            device = VcpFtdi(
                name=device_configuration[common.Key.NAME],
                device_id=device_configuration[common.Key.FTDI_ID],
                sensor=sensor,
                baud_rate=device_configuration[common.Key.BAUD_RATE],
                callback_func=self._callback,
                log=self.log,
            )
            return device
        elif device_configuration[common.Key.DEVICE_TYPE] == common.DeviceType.SERIAL:
            self.log.debug(
                f"Creating RpiSerialHat device with name {device_configuration[common.Key.NAME]} "
                f"and sensor {sensor}"
            )
            device = RpiSerialHat(
                name=device_configuration[common.Key.NAME],
                device_id=device_configuration[common.Key.SERIAL_PORT],
                sensor=sensor,
                baud_rate=device_configuration[common.Key.BAUD_RATE],
                callback_func=self._callback,
                log=self.log,
            )
            return device
        raise RuntimeError(
            f"Could not get a {device_configuration[common.Key.DEVICE_TYPE]!r} device."
            "Please check the configuration."
        )
