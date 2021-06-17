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

__all__ = ["BaseDevice", "DELIMITER", "TERMINATOR"]

from abc import ABC, abstractmethod
import asyncio
import logging
import time
from typing import Callable, List, Optional, Union

from ..constants import Key
from ..response_code import ResponseCode
from ..sensor import BaseSensor
from ..utils import create_done_future


"""Serial data channel delimiter."""
DELIMITER = ","

"""Serial data line terminator."""
TERMINATOR = "\r\n"


class BaseDevice(ABC):
    """Base class for the different types of Sensor Devices.

    This class holds all common code for the hardware devices. Device specific
    code (for instance for a serial or an FTDI device) needs to be implemented
    in a sub-class.

    Parameters:
    -----------
    name: `str`
        The name of the device.
    device_id: `str`
        The hardware device ID to connect to. This can be a physical ID (e.g.
        /dev/ttyUSB0), a serial port (e.g. serial_ch_1) or any other ID used by
        the specific device.
    sensor: `BaseSensor`
        The sensor that produces the telemetry.
    callback_func : `Callable`
        Callback function to receive the telemetry.
    log: `logging.Logger`
        The logger to create a child logger for.
    """

    @abstractmethod
    def __init__(
        self,
        name: str,
        device_id: str,
        sensor: BaseSensor,
        callback_func: Callable,
        log: logging.Logger,
    ) -> None:
        self.name: str = name
        self._device_id: str = device_id
        self._sensor: BaseSensor = sensor
        self._callback_func: Callable = callback_func
        self._telemetry_loop: asyncio.Future = create_done_future()
        self._log = log.getChild(type(self).__name__)

    @abstractmethod
    def init(self) -> None:
        """Initialize the Sensor Device."""
        pass

    @abstractmethod
    async def open(self) -> None:
        """Open the Sensor Device."""
        pass

    async def start(self) -> None:
        """Start the sensor read loop."""
        self._log.debug(f"Starting read loop for {self.name!r} sensor.")
        self._telemetry_loop = asyncio.create_task(self._run())

    async def _run(self) -> None:
        """Run sensor read loop.

        If enabled, loop and read the sensor and pass result to callback_func.
        """
        self._log.debug("Starting sensor.")
        await self._sensor.open()
        while not self._telemetry_loop.done():
            self._log.debug("Reading data.")
            tm: float = time.time()
            response: int = ResponseCode.OK
            line: str = await self.readline()
            sensor_telemetry: List[float] = await self._sensor.extract_telemetry(
                line=line
            )
            output: List[Union[str, int, float]] = [
                self.name,
                tm,
                response,
            ] + sensor_telemetry
            reply = {
                Key.TELEMETRY: output,
            }
            self._log.info(f"Returning {reply}")
            await self._callback_func(reply)

    @abstractmethod
    async def readline(self) -> str:
        """Read a line of telemetry from the Device.

        Returns
        -------
        output: `str`
            A line of telemetry.
        """
        pass

    async def stop(self) -> None:
        """Terminate the sensor read loop."""
        self._log.debug(f"Stopping read loop for {self.name!r} sensor.")
        self._telemetry_loop.cancel()
        self._telemetry_loop = create_done_future()
        await self._sensor.close()

    @abstractmethod
    async def close(self) -> None:
        """Close the Sensor Device."""
        pass
