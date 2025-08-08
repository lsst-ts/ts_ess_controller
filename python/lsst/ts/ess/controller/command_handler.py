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

__all__ = ["CommandHandler", "run_ess_controller"]

import logging
import typing
import asyncio

from lsst.ts.ess import common
from .device import RpiSerialHat, VcpFtdi


class CommandHandler(common.AbstractCommandHandler):
    valid_simulation_modes = (0, 1)

    def __init__(
        self,
        callback: typing.Callable[[typing.Any], None],
        simulation_mode: int = 0,
        use_csv: bool = False,
        csv_path: typing.Optional[str] = None,
        log: typing.Optional[logging.Logger] = None,
    ) -> None:
        self.callback = callback
        self.simulation_mode = simulation_mode
        self.use_csv = use_csv
        self.csv_path = csv_path
        self.log = log or logging.getLogger(__name__)  # always have a Logger

    def create_device(
        self,
        device_configuration: typing.Dict[str, typing.Any],
        devices_in_error_state: bool = False,
    ) -> common.device.BaseDevice:
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
                in_error_state=devices_in_error_state,
            )
            return device

        elif device_configuration[common.Key.DEVICE_TYPE] == common.DeviceType.FTDI:
            self.log.debug(
                f"Creating VcpFtdi device with name {device_configuration[common.Key.NAME]} "
                f"and sensor {sensor}"
            )
            return VcpFtdi(
                name=device_configuration[common.Key.NAME],
                device_id=device_configuration[common.Key.FTDI_ID],
                sensor=sensor,
                baud_rate=device_configuration[common.Key.BAUD_RATE],
                callback_func=self._callback,
                log=self.log,
            )

        elif device_configuration[common.Key.DEVICE_TYPE] == common.DeviceType.SERIAL:
            self.log.debug(
                f"Creating RpiSerialHat device with name {device_configuration[common.Key.NAME]} "
                f"and sensor {sensor}"
            )
            return RpiSerialHat(
                name=device_configuration[common.Key.NAME],
                device_id=device_configuration[common.Key.SERIAL_PORT],
                sensor=sensor,
                baud_rate=device_configuration[common.Key.BAUD_RATE],
                callback_func=self._callback,
                log=self.log,
            )

        elif device_configuration[common.Key.DEVICE_TYPE] == "CSV":
            csv_path = device_configuration.get("csv_path", "sensor_data.csv")
            self.log.debug(
                f"Creating CSVDevice with name {device_configuration[common.Key.NAME]} and path {csv_path}"
            )
            from lsst.ts.ess.common.device.csv_device import CSVDevice

            return CSVDevice(
                name=device_configuration[common.Key.NAME],
                csv_path=csv_path,
                sensor=sensor,
                callback_func=self._callback,
                log=self.log,
            )

        raise RuntimeError(
            f"Could not get a {device_configuration[common.Key.DEVICE_TYPE]!r} device. "
            "Please check the configuration."
        )

def run_ess_controller() -> None:
    """Main method that, when executed in stand alone mode, starts the socket
    server.

    The SocketServer automatically stops once the client exits and at that
    moment this script will exit as well.
    """
    asyncio.run(_run_ess_controller_impl())


async def _run_ess_controller_impl() -> None:
    """Async implementation of run_ess_controller."""

    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
        level=logging.INFO,
    )
    log = logging.getLogger()

    log.info("main method")
    host = "0.0.0.0"
    port = common.CONTROLLER_PORT
    log.info("Constructing the sensor server.")
    # Simulation mode 0 means "connect to the real sensors."
    # Set simulation_mode to 1 to enable simulation mode and connect to a mock
    # sensor.
    srv = common.SocketServer(
        name="EssSensorsServer", host=host, port=port, simulation_mode=0, log=log
    )
    command_handler = CommandHandler(callback=srv.write_json, simulation_mode=0)
    srv.set_command_handler(command_handler)
    log.info("Starting the sensor server.")
    await srv.start_task
    await srv.done_task
