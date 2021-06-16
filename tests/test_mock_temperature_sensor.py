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

from lsst.ts.envsensors.device.mock_device import MockDevice
from lsst.ts.envsensors.sensor.mock_temperature_sensor import MockTemperatureSensor
from base_mock_test_case import BaseMockTestCase

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class MockSensorTestCase(BaseMockTestCase):
    async def test_read_instrument(self):
        self.num_channels = 4
        self.disconnected_channel = None
        self.missed_channels = 0
        self.name = "MockSensor"
        self.log = logging.getLogger(type(self).__name__)
        mock_sensor = MockTemperatureSensor(self.name, self.num_channels, self.log)
        reply = await mock_sensor.readline()
        self.check_reply(reply=reply)

    async def test_read_partial_output(self):
        self.num_channels = 4
        self.missed_channels = 2
        self.disconnected_channel = None
        self.name = "MockSensor"
        self.log = logging.getLogger(type(self).__name__)
        mock_sensor = MockTemperatureSensor(
            self.name,
            self.num_channels,
            self.log,
            missed_channels=self.missed_channels,
        )
        reply = await mock_sensor.readline()
        self.check_reply(reply=reply)

    async def test_read_with_disconnected_channel(self):
        self.num_channels = 4
        self.disconnected_channel = 2
        self.missed_channels = 0
        self.name = "MockSensor"
        self.log = logging.getLogger(type(self).__name__)
        mock_sensor = MockTemperatureSensor(
            self.name,
            self.num_channels,
            self.log,
            self.disconnected_channel,
        )
        reply = await mock_sensor.readline()
        self.check_reply(reply=reply)
