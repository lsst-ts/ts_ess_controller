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

import asyncio
import logging
import math
import unittest

from lsst.ts.envsensors.sensor.base_sensor import DELIMITER, TERMINATOR
from lsst.ts.envsensors.sensor.wind_sensor import (
    WindSensor,
    DEFAULT_DIRECTION_VAL,
    DEFAULT_SPEED_VAL,
    DEFAULT_STATUS,
    END_CHARACTER,
    START_CHARACTER,
    UNIT_IDENTIFIER,
    WINDSPEED_UNIT,
)

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class WindSensorTestCase(unittest.IsolatedAsyncioTestCase):
    def get_line(self, speed: str, direction: str) -> str:
        """Create a line of output as can be expected from a wind sensor."""
        checksum_string: str = (
            UNIT_IDENTIFIER
            + DELIMITER
            + direction
            + DELIMITER
            + speed
            + DELIMITER
            + WINDSPEED_UNIT
            + DELIMITER
            + DEFAULT_STATUS
            + DELIMITER
        )
        checksum: int = 0
        for i in checksum_string:
            checksum ^= ord(i)
        line = (
            START_CHARACTER
            + UNIT_IDENTIFIER
            + DELIMITER
            + direction
            + DELIMITER
            + speed
            + DELIMITER
            + WINDSPEED_UNIT
            + DELIMITER
            + DEFAULT_STATUS
            + DELIMITER
            + END_CHARACTER
            + f"{checksum:02x}"
            + TERMINATOR
        )
        return line

    async def test_extract_telemetry(self) -> None:
        self.num_channels = 4
        self.disconnected_channel = None
        self.missed_channels = 0
        self.name = "WindSensor"
        self.log = logging.getLogger(type(self).__name__)
        wind_sensor = WindSensor(self.num_channels, self.log)

        wind_data = ("015.00", "010")
        line = self.get_line(speed=wind_data[0], direction=wind_data[1])
        reply = await wind_sensor.extract_telemetry(line=line)
        self.assertAlmostEqual(float(wind_data[0]), reply[0])
        self.assertAlmostEqual(float(wind_data[1]), reply[1])

        wind_data = ("001.00", "")
        line = self.get_line(speed=wind_data[0], direction=wind_data[1])
        reply = await wind_sensor.extract_telemetry(line=line)
        self.assertAlmostEqual(float(wind_data[0]), reply[0])
        self.assertTrue(math.isnan(reply[1]))
