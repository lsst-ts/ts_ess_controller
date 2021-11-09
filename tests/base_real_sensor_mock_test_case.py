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

__all__ = ["BaseRealSensorMockTestCase"]

import asyncio
import logging
import typing
import unittest

from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

# Read timeout [sec].
STD_TIMEOUT = 5.0


class BaseRealSensorMockTestCase(unittest.IsolatedAsyncioTestCase):
    """Test Case for mocking real hardware sensors. Subclasses need to
    implement test methods that replace the read method of the sensor with the
    read method in this class and then call the read_next method.

    Attributes
    ----------
    log : `logging.Logger`
        The logger.
    num_channels : `int`
        The number of channels of the sensor.
    sensor : `common.sensor.TemperatureSensor`
        The sensor.
    return_as_plain_text : `bool`
        Is the output string expected to be plain text (True) or byte encoded
        (False).
    mtt : `common.MockTestTools`
        Test tools for mock classes to ease testing the output of the sensor.
    """

    async def asyncSetUp(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.num_channels = 1
        self.sensor = common.sensor.TemperatureSensor(
            num_channels=self.num_channels, log=self.log
        )
        self.return_as_plain_text = True
        self.mtt = common.MockTestTools()

        self._sensor_output = None
        self._read_task: asyncio.Future = asyncio.Future()
        self._num_read_calls = 0

    async def _callback(
        self, reply: typing.Dict[str, typing.List[typing.Union[str, float]]]
    ) -> None:
        if not self._read_task.done():
            self._read_task.set_result(reply)
        self._sensor_output = None

    def read(self, length: int) -> str:
        """Mock reading sensor output.

        Parameters
        ----------
        length : `int`
            The number of characters to read. In the sensor code this is always
            set to 1 and this is asserted in this method.

        Returns
        -------
        `str`
            A plain text or byte encoded string representing the output of the
            sensor.
        """
        assert length == 1

        if self._sensor_output is None:
            formatter = common.device.MockTemperatureFormatter()
            self._sensor_output = (
                self.sensor.delimiter.join(
                    formatter.format_output(num_channels=self.num_channels)
                )
                + self.sensor.terminator
            )

        assert self._sensor_output is not None
        ch = self._sensor_output[self._num_read_calls]
        self._num_read_calls += 1

        # Reset the number of read calls to mock new sensor output.
        if self._num_read_calls >= len(self._sensor_output):
            self._num_read_calls = 0

        if self.return_as_plain_text:
            return ch
        else:
            return ch.encode(self.sensor.charset)

    async def read_next(self, timeout: float = STD_TIMEOUT) -> str:
        """Helper method to ease reading output from a mocked sensor.

        Parameters
        ----------
        timeout : `float`
            The timeout for reading the output.

        Returns
        -------
        `str`
            A plain text or byte encoded string representing the output of the
            sensor.
        """
        self._read_task = asyncio.Future()
        return await asyncio.wait_for(self._read_task, timeout=timeout)
