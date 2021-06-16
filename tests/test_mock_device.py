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
import unittest

from lsst.ts.envsensors.constants import Key, Temperature, DISCONNECTED_VALUE
from lsst.ts.envsensors.device.mock_device import MockDevice
from lsst.ts.envsensors.sensor.mock_temperature_sensor import MockTemperatureSensor
from base_mock_test_case import BaseMockTestCase

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class MockDeviceTestCase(BaseMockTestCase):
    async def _callback(self, reply):
        logging.info(f"Received reply {reply!r}")
        self.reply = reply

    async def test_mock_device(self):
        self.name = "MockSensor"
        self.num_channels = 4
        self.count_offset = 0
        self.disconnected_channel = None
        self.data = None
        self.log = logging.getLogger(type(self).__name__)
        mock_sensor = MockTemperatureSensor(
            name=self.name, channels=self.num_channels, log=self.log
        )
        mock_device = MockDevice(
            device_id="MockDevice",
            sensor=mock_sensor,
            callback_func=self._callback,
            log=self.log,
        )
        self.reply = None
        await mock_device.start()
        while not self.reply:
            await asyncio.sleep(0.1)
        await mock_device.stop()
        reply_to_check = self.reply[Key.TELEMETRY]
        self.check_reply(reply_to_check)
