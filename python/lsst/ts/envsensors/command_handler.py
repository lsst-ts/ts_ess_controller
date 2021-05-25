# This file is part of ts_envsensors.
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

import asyncio
import logging
import platform
import time
import typing

from .command_error import CommandError
from .ess_instrument_object import EssInstrument
from .mock.mock_temperature_sensor import MockTemperatureSensor
from .response_code import ResponseCode
from .sel_temperature_reader import SelTemperature


class ReceivedCommand:
    def __init__(self, sequence_number: int, command: str) -> None:
        self.sequence_number = sequence_number
        self.command = command
        self.received = time.time()
        self.replied = False


class CommandHandler:
    """Handle incoming commands and send replies. Apply configuration and read
    sensor data.

    Parameters
    ----------
    callback: `Callable`
        The callback coroutine handling the sensor telemetry. This can be a
        coroutine that sends the data via a socket connection or a coroutine in
        a test class to verify that the command has been handled correctly.
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

    def __init__(self, callback: typing.Callable, simulation_mode: int) -> None:
        self.log = logging.getLogger(type(self).__name__)
        if simulation_mode not in self.valid_simulation_modes:
            raise ValueError(
                f"simulation_mode={simulation_mode} "
                f"not in valid_simulation_modes={self.valid_simulation_modes}"
            )

        self.simulation_mode = simulation_mode

        self._callback = callback
        self._configuration: dict = None
        self._started = False
        self._ess_instruments = []

        self.dispatch_dict = {
            "configure": self.configure,
            "start": self.start_sending_telemetry,
            "stop": self.stop_sending_telemetry,
        }

        # Unit tests may set this to an integer value to simulate a
        # disconnected or missing sensor.
        self.disconnected_channel = None

    async def handle_command(self, command: str, **kwargs) -> None:
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
        try:
            await func(**kwargs)
            response = {"response": ResponseCode.OK}
        except CommandError as e:
            response = {"response": e.responce_code}
        await self._callback(response)

    async def configure(self, configuration: dict) -> None:
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
            raise CommandError(
                msg="Ignoring the configuration because telemetry loop already running. Send a stop first.",
                responce_code=ResponseCode.ALREADY_STARTED,
            )
        self._configuration = configuration

    async def start_sending_telemetry(self) -> None:
        """Connect the sensors and start reading the sensor data.

        Returns
        -------
        response_code: `ResponseCode`
            OK if the command handler was configured.
            NOT_CONFIGURED if the command handler was not configured.

        """
        self.log.info("start_sending_telemetry")
        if not self._configuration:
            raise CommandError(
                msg="No configuration has been received yet. Ignoring start command.",
                responce_code=ResponseCode.NOT_CONFIGURED,
            )
        await self.connect_devices()
        self._started = True

    async def connect_devices(self) -> None:
        """Loop over the configuration and start all devices."""
        # TODO: Implement misconfiguration handling (DM-30069)
        self.log.info("connect_devices")
        configured_devices = self._configuration["devices"]
        for configured_device in configured_devices:
            device = self._get_device(configured_device)
            sel_temperature = SelTemperature(
                name=configured_device["name"],
                uart_device=device,
                channels=configured_device["channels"],
                log=self.log,
            )
            ess_instrument = EssInstrument(
                name=configured_device["name"],
                reader=sel_temperature,
                callback_func=self._process_sensor_telemetry,
                log=self.log,
            )

            self._ess_instruments.append(ess_instrument)
            await ess_instrument.start()

    async def stop_sending_telemetry(self) -> ResponseCode:
        """Stop reading the sensor data.

        Returns
        -------
        response_code: `ResponseCode`
            OK if the command handler was started.
            NOT_STARTED if the command handler was not started.

        """
        self.log.info("stop_sending_telemetry")
        if not self._started:
            raise CommandError(
                msg="Not started yet. Ignoring stop command.",
                responce_code=ResponseCode.NOT_STARTED,
            )
        self._started = False
        for ess_instrument in self._ess_instruments:
            await ess_instrument.stop()
            self._ess_instruments.remove(ess_instrument)
        return ResponseCode.OK

    async def _process_sensor_telemetry(self, telemetry: list) -> None:
        """wrap the telemetry in a dictionary and pass it on to the callback
        coroutine.

        It is up to the callback coroutine to handle the telemetry further
        (e.g. in case of the SocketServer the telemetry gets sent to the
        client).

        Parameters
        ----------
        telemetry: `list`
            The telemetry data to send.
        """
        self.log.debug(f"Processing sensor data {telemetry}")
        data = {"telemetry": telemetry}
        await self._callback(data)

    def _get_device(self, configured_device: dict) -> typing.Optional[typing.Any]:
        """Get the device to connect to by using the _configuration of the CSC
        and by detecting whether the code is running on an aarch64 architecture
        or not.

        Parameters
        ----------
        configured_device: `dict`
            A dict representing the device to connect to. The format of the
            dict follows the configuration of the ts_ess project.

        Returns
        -------
        device: `MockTemperatureSensor` or `VcpFtdi` or `RpiSerialHat` or
            `None`
            The device to connect to.

        Raises
        ------
        RuntimeError
            In case an incorrect _configuration has been loaded.
        """
        device = None
        if self.simulation_mode == 1:
            self.log.info("Connecting to the mock sensor.")
            device = MockTemperatureSensor(
                configured_device["name"],
                configured_device["channels"],
                disconnected_channel=self.disconnected_channel,
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
