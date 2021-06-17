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

__all__ = ["WindSensor"]

import asyncio
import logging
import math
from typing import List, Optional, Union

from ..constants import DISCONNECTED_VALUE
from ..response_code import ResponseCode
from .base_sensor import BaseSensor, DELIMITER, TERMINATOR


class WindSensor(BaseSensor):
    """Wind Sensor.

    Parameters
    ----------
    name: `str`
        The name of the sensor.
    channels: `int`
        The number of temperature channels.
    log: `logger`' optional
        The logger for which to create a child logger, or None in which case a
        new logger gets requested.
    """

    def __init__(
        self,
        channels: int,
        log: logging.Logger,
    ) -> None:
        super().__init__(channels=channels, log=log)

    async def open(self) -> None:
        """Open a connection to the Sensor and set parameters."""
        # TODO: implementation will follow.
        pass

    async def extract_telemetry(self, line: str) -> List[float]:
        """Extract the wind telemetry from a line of Sensor data."""
        # TODO: implementation will follow.
        return []

    async def close(self) -> None:
        """Close the connection to the Sensor."""
        # TODO: implementation will follow.
        pass
