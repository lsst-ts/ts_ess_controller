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
from lsst.ts.ess.common.test_utils import MockTestTools

# Read timeout [sec].
STD_TIMEOUT = 5.0


class BaseRealSensorMockTestCase(unittest.IsolatedAsyncioTestCase):
    """Test Case for mocking real hardware sensors.

    Subclasses need to implement test methods that replace the read method of
    the sensor with the read method in this class and then call the
    wait_for_read_event method.

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
    mtt : `MockTestTools`
        Test tools for mock classes to ease testing the output of the sensor.
    """

    async def asyncSetUp(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.num_channels = 1
        self.sensor = common.sensor.TemperatureSensor(
            num_channels=self.num_channels, log=self.log
        )
        self.return_as_plain_text = True
        self.mtt = MockTestTools()

        self.device: common.device.BaseDevice | None = None

        self._sensor_output = None
        self._read_event: asyncio.Event = asyncio.Event()
        self._num_read_calls = 0
        self._reply: typing.Dict[str, typing.List[typing.Union[str, float]]] = {}
        self.add_null_character_in_terminator = False
        self.read_generates_error = False

    async def _callback(
        self, reply: typing.Dict[str, typing.List[typing.Union[str, float]]]
    ) -> None:
        self._reply = reply
        self._sensor_output = None

    async def wait_for_read_event(self, timeout: float = STD_TIMEOUT) -> None:
        """Clear the read event and then wait for it to be set again.

        It having been set again indicates new sensor data has been read.

        Parameters
        ----------
        timeout : `float`
            The timeout for reading the output.
        """
        assert self.device is not None
        self.log.debug("Clearing read event.")
        self.device.readline_event.clear()
        self.log.debug("Waiting for read event.")
        try:
            await asyncio.wait_for(self.device.readline_event.wait(), timeout=timeout)
            self.log.debug("Confirmed that read event has been set.")
            assert self.read_generates_error is False
        except TimeoutError:
            assert self.read_generates_error is True
