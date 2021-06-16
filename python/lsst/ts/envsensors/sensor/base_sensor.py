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

__all__ = ["BaseSensor", "DELIMITER", "TERMINATOR"]

from abc import ABC, abstractmethod
import logging
from typing import List, Union

"""Serial data line terminator."""
TERMINATOR = "\r\n"

"""Serial data channel delimiter."""
DELIMITER = ","


class BaseSensor(ABC):
    """Base class for the different types of Sensors.

    This class holds all common code for the sensors. Sensor specific code
    (for instance temperature, humidity or wind sensor) needs to be implemented
    in a sub-class.

    Parameters:
    -----------
    name: `str`
        The name of the sensor.
    channels: `int`
        The number of channels that the sensor will produce telemetry for.
    """

    @abstractmethod
    def __init__(self, name: str, channels: int, log: logging.Logger) -> None:
        self.name: str = name
        self._channels: int = channels
        self._log = log.getChild(type(self).__name__)
        self.terminator: str = TERMINATOR

    @abstractmethod
    async def readline(self) -> List[Union[str, int, float]]:
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
        pass

    @abstractmethod
    async def open(self) -> None:
        """Open a connection to the Sensor and set parameters."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the connection to the Sensor."""
        pass
