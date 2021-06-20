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

__all__ = ["TemperatureSensor"]

import asyncio
import logging
import math
from typing import List, Optional, Union

from ..constants import DISCONNECTED_VALUE
from ..response_code import ResponseCode
from .base_sensor import BaseSensor, DELIMITER, TERMINATOR


class TemperatureSensor(BaseSensor):
    """Temperature Sensor.

    Parameters
    ----------
    name: `str`
        The name of the sensor.
    num_channels: `int`
        The number of temperature channels.
    log: `logger`' optional
        The logger for which to create a child logger, or None in which case a
        new logger gets requested.
    """

    def __init__(
        self,
        num_channels: int,
        log: logging.Logger,
    ) -> None:
        super().__init__(num_channels=num_channels, log=log)

    async def extract_telemetry(self, line: str) -> List[float]:
        """Extract the temperature telemetry from a line of Sensor data.

        Parameters
        ----------
        line: `str`
            A line of comma separated telemetry, each of the format
            CXX=XXXX.XXX

        Returns
        -------
        output: `list`
            A list containing the temperature telemetry as measured by the
            specific type of sensor. The length of the output list is the same
            as the number of channels.
            If a channel is disconnected (its value will be DISCONNECTED_VALUE)
            or if a channel is missing then the value gets replaced by math.nan
        """
        self._log.debug("extract_telemetry")
        stripped_line: str = line.strip(TERMINATOR)
        line_items = stripped_line.split(DELIMITER)
        output = []
        for line_item in line_items:
            temperature_items = line_item.split("=")
            if len(temperature_items) == 1:
                output.append(math.nan)
            elif len(temperature_items) == 2:
                if temperature_items[1] == DISCONNECTED_VALUE:
                    output.append(math.nan)
                else:
                    output.append(float(temperature_items[1]))
            else:
                raise ValueError(
                    f"At most one '=' symbol expected in temperature item {line_item}"
                )

        # When the connection is first made, it may be done while the sensor is
        # in the middle of outputting data. In that case, only a partial string
        # witht he final channels will be received and the missing leading
        # channels need to be filled with NaN.
        while len(output) < self.num_channels:
            output.insert(0, math.nan)
        return output
