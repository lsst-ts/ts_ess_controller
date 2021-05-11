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

import unittest
import asyncio

from lsst.ts.ess.sensors.ess_instrument_object import EssInstrument
from lsst.ts.ess.sensors.sel_temperature_reader import SelTemperature
from lsst.ts.ess.sensors.mock.mock_temperature_sensor import MockTemperatureSensor


class EssInstrumentObjectTestCase(unittest.IsolatedAsyncioTestCase):
    async def _callback(self, data):
        self.assertEqual(self.num_channels + 3, len(data))
        self.assertEqual(self.name, data[0])
        for i in range(0, self.num_channels):
            data_item = data[i + 3]
            if self.disconnected_channel and i == self.disconnected_channel:
                self.assertAlmostEqual(
                    float(MockTemperatureSensor.DISCONNECTED_VALUE), float(data_item), 3
                )
            else:
                self.assertTrue(
                    MockTemperatureSensor.MIN_TEMP
                    <= float(data_item)
                    <= MockTemperatureSensor.MAX_TEMP
                )
        self.ess_instrument._enabled = False

    async def test_ess_instrument_object(self):
        self.num_channels = 4
        self.disconnected_channel = None
        self.name = "MockSensor"
        device = MockTemperatureSensor(self.name, self.num_channels)
        sel_temperature = SelTemperature(self.name, device, self.num_channels)
        await sel_temperature.start()
        self.ess_instrument = EssInstrument(
            self.name, sel_temperature, callback_func=self._callback
        )
        self.ess_instrument._enabled = True
        await self.ess_instrument._run()

    async def test_old_ess_instrument_object(self):
        self.num_channels = 4
        count_offset = 1
        self.disconnected_channel = None
        self.name = "MockSensor"
        device = MockTemperatureSensor(self.name, self.num_channels, count_offset)
        sel_temperature = SelTemperature(self.name, device, self.num_channels)
        await sel_temperature.start()
        self.ess_instrument = EssInstrument(
            self.name, sel_temperature, callback_func=self._callback
        )
        self.ess_instrument._enabled = True
        await self.ess_instrument._run()

    async def test_nan_ess_instrument_object(self):
        self.num_channels = 4
        count_offset = 1
        self.disconnected_channel = 2
        self.name = "MockSensor"
        device = MockTemperatureSensor(
            self.name, self.num_channels, count_offset, self.disconnected_channel
        )
        sel_temperature = SelTemperature(self.name, device, self.num_channels)
        await sel_temperature.start()
        self.ess_instrument = EssInstrument(
            self.name, sel_temperature, callback_func=self._callback
        )
        self.ess_instrument._enabled = True
        await self.ess_instrument._run()
