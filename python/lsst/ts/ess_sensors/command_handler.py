# This file is part of ts_ess_sensors.
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

__all__ = ["CommandHandler"]

import asyncio
import logging
import platform

from .ess_instrument_object import EssInstrument
from .mock.mock_temperature_sensor import MockTemperatureSensor
from .response_code import ResponseCode
from .sel_temperature_reader import SelTemperature


class CommandHandler:
    """Handle incoming commands and send replies. Apply configuration and read
    sensor data.

    Parameters
    ----------
    callback: coroutine
        The callback coroutine used for sending replies, for insatnce for
        indicating if the command has been executed successfully or not or for
        sending telemetry.
    simulation_mode: `int`
        Indicating if a simulation mode (> 0) or not (0) is active.

    The commands that can be handled are:

        configure: Load the _configuration that is passed on with the command
        and connect to the devices specified in that _configuration. This
        command can be sent multiple times before a start is received and only
        the last _configuration is kept.
        start: Start reading the sensor data of the connected devices and send
        it as plain text via the socket. If no _configuration was sent then the
        start command is ignored. Once started no _configuration changes can be
        done anymore.
        stop: Stop sending sensor data and disconnect from all devices. Once
        stopped, _configuration changes can be done again and/or reading of
        sensor data can be started again.

    """

    valid_simulation_modes = (0, 1)

    def __init__(self, callback, simulation_mode):
        self.log = logging.getLogger(type(self).__name__)
        if simulation_mode not in self.valid_simulation_modes:
            raise ValueError(
                f"simulation_mode={simulation_mode} "
                f"not in valid_simulation_modes={self.valid_simulation_modes}"
            )

        self.simulation_mode = simulation_mode

        self.callback = callback
        self._configuration = None
        self._started = False
        self._ess_instruments = []

        self.dispatch_dict = {
            "configure": self.configure,
            "start": self.start_sending_telemetry,
            "stop": self.stop_sending_telemetry,
        }

        # Unit tests may set this to an integer value to simulate a
        # disconnected or missing sensor.
        self.nan_channel = None

    async def handle_command(self, command, **kwargs):
        """Handle incomming commands and parameters.

        Parameters
        ----------
        command: `str`
            The command to handle.
        kwargs:
            The parameters to the command.
        """
        self.log.info(f"Handling command {command} with kwargs {kwargs}")
        func = self.dispatch_dict[command]
        response_code = await func(**kwargs)
        response = {"response": response_code}
        await self.callback(response)

    async def configure(self, configuration):
        """Apply the configuration.

        Parameters
        ----------
        configuration: `dict`
            The contents of the dict depend on the type of sensor. See the
            ts_ess configuration schema for more details.

        Returns
        -------
        response_code: `ResponseCode`
            OK if the command handler was not started.
            ALREADY_STARTED if the command handler was started.

        """
        # TODO: Implement misconfiguration handling (DM-30069)
        self.log.info(f"configure with _configuration data {configuration}")
        if self._started:
            self.log.error(
                "Ignoring the configuration because telemetry loop already "
                "running. Send a stop first."
            )
            return ResponseCode.ALREADY_STARTED
        self._configuration = configuration
        return ResponseCode.OK

    async def start_sending_telemetry(self):
        """Connect the sensors and start reading the sensor data.

        Returns
        -------
        response_code: `ResponseCode`
            OK if the command handler was configured.
            NOT_CONFIGURED if the command handler was not configured.

        """
        self.log.info("start_sending_telemetry")
        if not self._configuration:
            self.log.error(
                "No configuration has been received yet. Ignoring start command."
            )
            return ResponseCode.NOT_CONFIGURED
        await self.connect_devices()
        self._started = True
        return ResponseCode.OK

    async def connect_devices(self):
        # TODO: Implement misconfiguration handling (DM-30069)
        """Loop over the configuration and start all devices."""
        self.log.info("connect_devices")
        configured_devices = self._configuration["devices"]
        for configured_device in configured_devices:
            device = self._get_device(configured_device)
            sel_temperature = SelTemperature(
                configured_device["name"],
                device,
                configured_device["channels"],
                self.log,
            )
            ess_instrument = EssInstrument(
                configured_device["name"],
                sel_temperature,
                self.callback,
                self.log,
            )

            self._ess_instruments.append(ess_instrument)
            await ess_instrument.start()

    async def stop_sending_telemetry(self):
        """Stop reading the sensor data.

        Returns
        -------
        response_code: `ResponseCode`
            OK if the command handler was started.
            NOT_STARTED if the command handler was not started.

        """
        self.log.info("stop_sending_telemetry")
        if not self._started:
            self.log.error("Not started yet. Ignoring stop command.")
            return ResponseCode.NOT_STARTED
        self._started = False
        for ess_instrument in self._ess_instruments:
            await ess_instrument.stop()
            self._ess_instruments.remove(ess_instrument)
        return ResponseCode.OK

    def _get_device(self, configured_device):
        """Get the device to connect to by using the _configuration of the CSC
        and by detecting whether the code is running on an aarch64 architecture
        or not.

        Returns
        -------
        device: `MockTemperatureSensor` or `VcpFtdi` or `RpiSerialHat` or
            `None`

        Raises
        ------
        RuntimeError
            In case an incorrect _configuration has been loaded.
        """
        device = None
        if self.simulation_mode == 1:
            self.log.info("Connecting to the mock sensor.")
            device = MockTemperatureSensor(
                configured_device["name"], 4, nan_channel=self.nan_channel
            )
        elif configured_device["type"] == "FTDI":
            from .vcp_ftdi import VcpFtdi

            device = VcpFtdi(
                configured_device["name"], configured_device["ftdi_id"], self.log
            )
        elif self.config.type == "Serial":
            # make sure we are on a Raspberry Pi4
            if "aarch64" in platform.platform():
                from .rpi_serial_hat import RpiSerialHat

                device = RpiSerialHat(
                    configured_device["name"], configured_device["port"], self.log
                )

        if device is None:
            raise RuntimeError(
                f"Could not get a {self.config.type!r} device on architecture "
                f"{platform.platform()}. Please check the _configuration."
            )
        return device
