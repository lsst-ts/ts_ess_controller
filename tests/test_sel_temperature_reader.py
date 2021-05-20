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

import unittest

from lsst.ts.envsensors.sel_temperature_reader import SelTemperature
from lsst.ts.envsensors.mock.mock_temperature_sensor import MockTemperatureSensor


class SelTemperatureReaderTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_sel_temperature_reader(self):
        num_channels = 4
        name = "MockSensor"
        device = MockTemperatureSensor(name, num_channels)
        sel_temperature = SelTemperature(name, device, num_channels)
        await sel_temperature.start()
        await sel_temperature.read()
        data = sel_temperature.output
        self.assertEqual(num_channels + 3, len(data))
        self.assertEqual(name, data[0])
        for i in range(0, 4):
            data_item = data[i + 3]
            assert (
                MockTemperatureSensor.MIN_TEMP
                <= float(data_item)
                <= MockTemperatureSensor.MAX_TEMP
            )
        await sel_temperature.stop()

    async def test_old_sel_temperature_reader(self):
        num_channels = 4
        count_offset = 1
        name = "MockSensor"
        device = MockTemperatureSensor(name, num_channels, count_offset)
        sel_temperature = SelTemperature(name, device, num_channels)
        await sel_temperature.start()
        await sel_temperature.read()
        data = sel_temperature.output
        self.assertEqual(num_channels + 3, len(data))
        self.assertEqual(name, data[0])
        for i in range(0, 4):
            data_item = data[i + 3]
            assert (
                MockTemperatureSensor.MIN_TEMP
                <= float(data_item)
                <= MockTemperatureSensor.MAX_TEMP
            )
        await sel_temperature.stop()

    async def test_nan_sel_temperature_reader(self):
        num_channels = 4
        count_offset = 1
        disconnected_channel = 2
        name = "MockSensor"
        device = MockTemperatureSensor(
            name, num_channels, count_offset, disconnected_channel=disconnected_channel
        )
        sel_temperature = SelTemperature(name, device, num_channels)
        await sel_temperature.start()
        await sel_temperature.read()
        data = sel_temperature.output
        self.assertEqual(num_channels + 3, len(data))
        self.assertEqual(name, data[0])
        for i in range(0, 4):
            data_item = data[i + 3]
            if i == disconnected_channel:
                self.assertAlmostEqual(
                    float(MockTemperatureSensor.DISCONNECTED_VALUE), float(data_item), 3
                )
            else:
                assert (
                    MockTemperatureSensor.MIN_TEMP
                    <= float(data_item)
                    <= MockTemperatureSensor.MAX_TEMP
                )
        await sel_temperature.stop()
