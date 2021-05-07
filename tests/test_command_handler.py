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
import json
import logging
import unittest

from lsst.ts.ess_sensors import CommandHandler, ResponseCode
from lsst.ts.ess_sensors.mock.mock_temperature_sensor import MIN_TEMP, MAX_TEMP

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class CommandHandlerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.command_handler = CommandHandler(callback=self.callback, simulation_mode=1)
        self.assertIsNone(self.command_handler._configuration)
        self.configuration = {
            "devices": [
                {
                    "name": "Test1",
                    "channels": 4,
                    "type": "FTDI",
                    "ftdi_id": "ABC",
                }
            ]
        }
        self.response = None

    async def callback(self, response):
        self.response = response

    async def test_configure(self):
        await self.command_handler.handle_command(
            command="configure", configuration=self.configuration
        )
        self.assertEqual(self.response["response"], ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)

    async def test_start(self):
        await self.command_handler.handle_command(command="start")
        self.assertEqual(self.response["response"], ResponseCode.NOT_CONFIGURED)
        self.assertIsNone(self.command_handler._configuration)
        self.assertFalse(self.command_handler._started)

        await self.command_handler.handle_command(
            command="configure", configuration=self.configuration
        )
        self.assertEqual(self.response["response"], ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)
        await self.command_handler.handle_command(command="start")
        self.assertEqual(self.response["response"], ResponseCode.OK)
        self.assertTrue(self.command_handler._started)

    async def test_stop(self):
        await self.command_handler.handle_command(command="stop")
        self.assertEqual(self.response["response"], ResponseCode.NOT_STARTED)
        self.assertIsNone(self.command_handler._configuration)
        self.assertFalse(self.command_handler._started)

        await self.command_handler.handle_command(
            command="configure", configuration=self.configuration
        )
        self.assertEqual(self.response["response"], ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)
        await self.command_handler.handle_command(command="start")
        self.assertEqual(self.response["response"], ResponseCode.OK)
        self.assertTrue(self.command_handler._started)

        await self.command_handler.handle_command(command="stop")
        self.assertEqual(self.response["response"], ResponseCode.OK)
        # Give time to the telemetry_task to get cancelled.
        await asyncio.sleep(0.5)
        self.assertFalse(self.command_handler._started)

    async def test_get_telemetrey(self):
        await self.command_handler.handle_command(
            command="configure", configuration=self.configuration
        )
        self.assertEqual(self.response["response"], ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)
        await self.command_handler.handle_command(command="start")
        self.assertEqual(self.response["response"], ResponseCode.OK)
        self.assertTrue(self.command_handler._started)

        await asyncio.sleep(2)
        # TODO: Properly support multiple sensors (DM-30070)
        config = self.configuration["devices"][0]
        for i in range(3, config["channels"] + 3):
            self.assertTrue(MIN_TEMP <= self.response[i] <= MAX_TEMP)

        await self.command_handler.handle_command(command="stop")
        self.assertEqual(self.response["response"], ResponseCode.OK)
        # Give time to the telemetry_task to get cancelled.
        await asyncio.sleep(0.5)
        self.assertFalse(self.command_handler._started)
