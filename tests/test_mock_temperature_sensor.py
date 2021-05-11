# This file is part of ts_ess_sensors.
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

import asyncio
import unittest

from lsst.ts.ess.sensors.mock.mock_temperature_sensor import MockTemperatureSensor


class MockTestCase(unittest.IsolatedAsyncioTestCase):
    def check_data(self, data, num_channels, count_offset, disconnected_channel):
        self.assertEqual(len(data), num_channels)
        for i in range(0, num_channels):
            data_item = data[i].split("=")
            self.assertTrue(f"C{i + count_offset:02d}", data_item[0])
            if i == disconnected_channel:
                self.assertAlmostEqual(
                    float(MockTemperatureSensor.DISCONNECTED_VALUE),
                    float(data_item[1]),
                    3,
                )
            else:
                self.assertLessEqual(
                    MockTemperatureSensor.MIN_TEMP, float(data_item[1])
                )
                self.assertLessEqual(
                    float(data_item[1]), MockTemperatureSensor.MAX_TEMP
                )

    async def test_read_instrument(self):
        num_channels = 4
        count_offset = 0
        disconnected_channel = None
        name = "MockSensor"
        ess_sensor = MockTemperatureSensor(name, num_channels)
        ess_sensor.terminator = "\r\n"
        loop = asyncio.get_event_loop()
        device_name, err, resp = await loop.run_in_executor(None, ess_sensor.readline)
        self.assertEqual(name, device_name)
        resp = resp.strip(ess_sensor.terminator)
        data = resp.split(",")
        self.check_data(data, num_channels, count_offset, disconnected_channel)

    async def test_read_old_instrument(self):
        num_channels = 4
        count_offset = 1
        disconnected_channel = None
        name = "MockSensor"
        ess_sensor = MockTemperatureSensor(name, num_channels, count_offset)
        ess_sensor.terminator = "\r\n"
        loop = asyncio.get_event_loop()
        device_name, err, resp = await loop.run_in_executor(None, ess_sensor.readline)
        self.assertEqual(name, device_name)
        resp = resp.strip(ess_sensor.terminator)
        data = resp.split(",")
        self.check_data(data, num_channels, count_offset, disconnected_channel)

    async def test_read_nan(self):
        num_channels = 4
        count_offset = 1
        disconnected_channel = 2
        name = "MockSensor"
        ess_sensor = MockTemperatureSensor(
            name, num_channels, count_offset, disconnected_channel
        )
        ess_sensor.terminator = "\r\n"
        loop = asyncio.get_event_loop()
        device_name, err, resp = await loop.run_in_executor(None, ess_sensor.readline)
        self.assertEqual(name, device_name)
        resp = resp.strip(ess_sensor.terminator)
        data = resp.split(",")
        self.check_data(data, num_channels, count_offset, disconnected_channel)
