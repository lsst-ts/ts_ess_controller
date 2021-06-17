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

__all__ = [
    "WindSensor",
    "DEFAULT_DIRECTION_VAL",
    "DEFAULT_SPEED_VAL",
    "DEFAULT_STATUS",
    "END_CHARACTER",
    "START_CHARACTER",
    "UNIT_IDENTIFIER",
    "WINDSPEED_UNIT",
]

import asyncio
import logging
import math
from typing import List, Optional, Union

from ..constants import DISCONNECTED_VALUE
from ..response_code import ResponseCode
from .base_sensor import BaseSensor, DELIMITER, TERMINATOR

"""ASCII start character."""
START_CHARACTER: str = "\x02"

"""Unit Identifier."""
UNIT_IDENTIFIER: str = "Q"

"""Windspeed unit."""
WINDSPEED_UNIT: str = "M"

"""Default status."""
DEFAULT_STATUS: str = "00"

"""ASCII end charactor."""
END_CHARACTER = "\x03"

"""Default value for the wind direction."""
DEFAULT_DIRECTION_VAL: float = 999

"""Default value for the wind speed."""
DEFAULT_SPEED_VAL: float = 9999.9990


class WindSensor(BaseSensor):
    """Wind Sensor.

    Perform protocol conversion for Gill Windsonic Ultrasonic Anemometer
    instrument. The instrument is assumed to use its default message format -
    "Gill - Polar, Continuous" as documented in Gill Windsonic Doc No 1405 PS
    0019 Issue 28.
    Serial data is output by the anemometer once per second with the following
    format:

        <STX>Q,ddd,sss.ss,M,00,<ETX>checksum<CR><LF>'

    where:

        <STX>       ASCII start character.
        'Q'         Unit Identifier ('Q' is default value).
        ddd         Wind direction. Three character, leading zero's integer.
                    000-359 degrees. Wind direction value is empty ('') when
                    wind speed is below 0.05 m/s.
        sss.ss      Wind speed. Six character, floating point, leading zero's.
                    0 to 60 m/s.
        'M'         Unit of speed measurement ('M' is m/s default)
        '00'        Status.
        <ETX>       ASCII end charactor.
        checksum    Exclusive OR of all bytes in the string between <STX> and
                    <ETX> characters.
        <CR><LF>    2-character terminator ('\r\n').

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

    async def extract_telemetry(self, line: str) -> List[float]:
        """Extract the wind telemetry from a line of Sensor data."""
        resp = line.strip(TERMINATOR)
        data = resp.split(DELIMITER)
        speed = DEFAULT_SPEED_VAL
        direction = DEFAULT_DIRECTION_VAL
        if len(data) == 6:
            if (
                data[0] == START_CHARACTER + UNIT_IDENTIFIER
                and data[3] == WINDSPEED_UNIT
                and data[4] == DEFAULT_STATUS
                and data[5][0] == END_CHARACTER
            ):
                csum_test_str = resp[1:-3]
                csum_val = int(resp[-2:], 16)
                checksum: int = 0
                for i in csum_test_str:
                    checksum ^= ord(i)
                if checksum == csum_val:
                    speed = float(data[2])
                    if not data[1] == "":
                        direction = float(data[1])
        if speed == DEFAULT_SPEED_VAL:
            speed = math.nan
        if direction == DEFAULT_DIRECTION_VAL:
            direction = math.nan
        return [speed, direction]
