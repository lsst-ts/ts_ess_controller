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

__all__ = ["MockDevice"]

import asyncio
import logging
import random
from typing import Callable

from .base_device import BaseDevice, DELIMITER, TERMINATOR
from ..constants import DISCONNECTED_VALUE, Temperature
from ..sensor import BaseSensor


class MockDevice(BaseDevice):
    """Mock Sensor Device.

    Parameters:
    -----------
    name: `str`
        The name of the device.
    device_id: `str`
        The hardware device ID to connect to.
    sensor: `BaseSensor`
        The sensor that produces the telemetry.
    callback_func : `Callable`
        Callback function to receive the telemetry.
    _disconnected_channel: `int`, optional
        The channels number for which this class will mock a disconnection.
    missed_channels: `int`, optional
        The number of channels to not output to mock connecting to the sensor
        in the middle of receiving data from it.
    """

    def __init__(
        self,
        name: str,
        device_id: str,
        sensor: BaseSensor,
        callback_func: Callable,
        log: logging.Logger,
        disconnected_channel: int = None,
        missed_channels: int = 0,
    ) -> None:
        super().__init__(
            name=name,
            device_id=device_id,
            sensor=sensor,
            callback_func=callback_func,
            log=log,
        )
        self._disconnected_channel = disconnected_channel
        self._missed_channels = missed_channels

    def init(self) -> None:
        """Initialize the Sensor Device."""
        pass

    async def open(self) -> None:
        """Open the Sensor Device."""
        pass

    def _format_temperature(self, i: int):
        """Creates a formatted string representing a temperature for the given
        channel.
        Parameters
        ----------
        i: `int`
            The temperature channel.
        Returns
        -------
        s: `str`
            A string representing a temperature.
        """
        temp = random.uniform(Temperature.MIN, Temperature.MAX)
        if i < self._missed_channels:
            return ""
        if i == self._disconnected_channel:
            return f"C{i:02d}={DISCONNECTED_VALUE}"
        return f"C{i:02d}={temp:09.4f}"

    async def readline(self) -> str:
        """Read a line of telemetry from the Device.

        Returns
        -------
        output: `str`
            A line of comma separated telemetry, each of the format
            CXX=XXXX.XXX
        """
        # Mock the time needed to output telemetry.
        await asyncio.sleep(1)
        channel_strs = [
            self._format_temperature(i) for i in range(0, self._sensor.channels)
        ]
        # Reset self._missed_channels because truncated data only happens when
        # data is being output while connecting.
        self._missed_channels = 0
        return DELIMITER.join(channel_strs) + TERMINATOR

    async def close(self) -> None:
        """Close the Sensor Device."""
        pass
