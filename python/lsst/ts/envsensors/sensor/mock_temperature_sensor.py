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

__all__ = ["MockTemperatureSensor"]

import asyncio
import logging
import math
import random
import time
from typing import List, Optional, Union

from ..constants import Temperature, DISCONNECTED_VALUE
from ..response_code import ResponseCode
from .base_sensor import BaseSensor, DELIMITER


class MockTemperatureSensor(BaseSensor):
    """Mock Temperature Sensor.

    Parameters
    ----------
    name: `str`
        The name of the sensor.
    channels: `int`
        The number of temperature channels.
    log: `logger`' optional
        The logger for which to create a child logger, or None in which case a
        new logger gets requested.
    disconnected_channel: `int`, optional
        The channels number for which this class will mock a disconnection.
    missed_channels: `int`, optional
        The number of channels to not output to mock connecting to the sensor
        in the middle of receiving data from it.
    """

    def __init__(
        self,
        name: str,
        channels: int,
        log: logging.Logger,
        disconnected_channel: int = None,
        missed_channels: int = 0,
    ) -> None:
        super().__init__(name=name, channels=channels, log=log)
        self._disconnected_channel: Optional[int] = disconnected_channel
        self._missed_channels: int = missed_channels

    async def open(self) -> None:
        """Open a connection to the Sesnor and set parameters."""
        pass

    async def close(self) -> None:
        """Close the connection to the Sesnor."""
        pass

    def _format_temperature(self, i: int) -> str:
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
        # Mock a disconnected sensor. A real sensor would output 9999.999 and
        # the real sensor code replaces that with math.nan
        if i == self._disconnected_channel:
            return math.nan
        # Mock connecting to the sensor in the middle of its output. For a real
        # sensor the value would be missing and the real sensor code adds
        # math.nan values for those.
        if i < self._missed_channels:
            return math.nan
        return temp

    async def readline(self) -> List[Union[str, float]]:
        """Read a line of telemetry from the Sensor.

        Returns
        -------
        output: `list`
            A list containing the timestamp, error and temperatures as
            measured by the sensor. The order of the items in the list is:
            - Sensor name: `str`
            - Timestamp: `float`
            - Response code: `int`
            - One or more sensor data: `float`
        """
        self._log.debug("Readline")
        await asyncio.sleep(1)
        tm: float = time.time()
        response: str = ResponseCode.OK
        channel_strs = [self._format_temperature(i) for i in range(0, self._channels)]
        if self._missed_channels > 0:
            # reset self._missed_channels since only the first read will be
            # truncated
            self._missed_channels = 0
        self._log.debug(f"Returning {self.name}, {tm}, {response}, {channel_strs}")
        return [self.name, tm, response] + channel_strs
