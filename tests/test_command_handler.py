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

from lsst.ts.envsensors import (
    CommandError,
    CommandHandler,
    ResponseCode,
    Command,
    DeviceType,
    Key,
)
from lsst.ts.envsensors.device_config import DeviceConfig
from lsst.ts.envsensors.mock.mock_temperature_sensor import MockTemperatureSensor

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class CommandHandlerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.command_handler = CommandHandler(callback=self.callback, simulation_mode=1)
        self.assertIsNone(self.command_handler._configuration)
        device_config_01 = DeviceConfig(
            name="Test01", channels=4, dev_type=DeviceType.FTDI, dev_id="ABC"
        )
        device_config_02 = DeviceConfig(
            name="Test02", channels=6, dev_type=DeviceType.FTDI, dev_id="ABC"
        )
        device_config_03 = DeviceConfig(
            name="Test03", channels=2, dev_type=DeviceType.FTDI, dev_id="ABC"
        )
        self.configuration = {
            Key.DEVICES: [
                device_config_01.as_dict(),
                device_config_02.as_dict(),
                device_config_03.as_dict(),
            ]
        }
        self.device_configs = {
            device_config_01.name: device_config_01,
            device_config_02.name: device_config_02,
            device_config_03.name: device_config_03,
        }
        self.responses = []

    async def callback(self, response):
        self.responses.append(response)

    def assert_response(self, response_code):
        response = self.responses.pop()
        self.assertEqual(response[Key.RESPONSE], response_code)

    async def test_configure(self):
        await self.command_handler.handle_command(
            command=Command.CONFIGURE, configuration=self.configuration
        )
        self.assert_response(ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)

        configuration = {
            "Key.DEVICES": [
                {
                    Key.NAME: "Test1",
                },
                {
                    Key.NAME: "Test1",
                    Key.CHANNELS: 4,
                },
                {
                    Key.NAME: "Test1",
                    Key.CHANNELS: 4,
                    Key.TYPE: DeviceType.FTDI,
                    "id": "ABC",
                },
                {
                    Key.NAME: "Test1",
                    Key.CHANNELS: 4,
                    Key.TYPE: DeviceType.SERIAL,
                    "port": "ABC",
                },
            ]
        }
        await self.command_handler.handle_command(
            command=Command.CONFIGURE, configuration=configuration
        )
        self.assert_response(ResponseCode.INVALID_CONFIGURATION)

        # A more extensive, but still good, configuration.
        good_configuration = {
            Key.DEVICES: [
                {
                    Key.NAME: "Test1",
                    Key.CHANNELS: 4,
                    Key.TYPE: DeviceType.FTDI,
                    Key.FTDI_ID: "ABC",
                },
                {
                    Key.NAME: "Test2",
                    Key.CHANNELS: 6,
                    Key.TYPE: DeviceType.SERIAL,
                    Key.SERIAL_PORT: "DEF",
                },
            ]
        }
        await self.command_handler.handle_command(
            command=Command.CONFIGURE, configuration=good_configuration
        )
        self.assert_response(ResponseCode.OK)

        # The value for Key.DEVICES may not be empty.
        bad_configuration = {Key.DEVICES: []}
        await self.command_handler.handle_command(
            command=Command.CONFIGURE, configuration=configuration
        )
        self.assert_response(ResponseCode.INVALID_CONFIGURATION)

        # A configuration with several errors that will get tested one by one.
        bad_items = [
            {
                # The mandatory keys Key.CHANNELS and Key.TYPE are missing.
                Key.NAME: "Test1",
            },
            {
                # The mandatory key Key.TYPE is missing.
                Key.NAME: "Test1",
                Key.CHANNELS: 4,
            },
            {
                # For DeviceType.FTDI the key Key.FTDI_ID is mandatory.
                Key.NAME: "Test1",
                Key.CHANNELS: 4,
                Key.TYPE: DeviceType.FTDI,
                "id": "ABC",
            },
            {
                # For DeviceType.SERIAL the key Key.SERIAL_PORT is mandatory.
                Key.NAME: "Test1",
                Key.CHANNELS: 4,
                Key.TYPE: DeviceType.SERIAL,
                "port": "ABC",
            },
        ]
        for bad_item in bad_items:
            bad_configuration = good_configuration.copy()
            bad_configuration[Key.DEVICES].append(bad_item)
            await self.command_handler.handle_command(
                command=Command.CONFIGURE, configuration=configuration
            )
            self.assert_response(ResponseCode.INVALID_CONFIGURATION)

    async def test_start(self):
        await self.command_handler.handle_command(command=Command.START)
        self.assert_response(ResponseCode.NOT_CONFIGURED)
        self.assertIsNone(self.command_handler._configuration)
        self.assertFalse(self.command_handler._started)

        await self.command_handler.handle_command(
            command=Command.CONFIGURE, configuration=self.configuration
        )
        self.assert_response(ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)
        await self.command_handler.handle_command(command=Command.START)
        self.assert_response(ResponseCode.OK)
        self.assertTrue(self.command_handler._started)

    async def test_stop(self):
        await self.command_handler.handle_command(command=Command.STOP)
        self.assert_response(ResponseCode.NOT_STARTED)
        self.assertIsNone(self.command_handler._configuration)
        self.assertFalse(self.command_handler._started)

        await self.command_handler.handle_command(
            command=Command.CONFIGURE, configuration=self.configuration
        )
        self.assert_response(ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)
        await self.command_handler.handle_command(command=Command.START)
        self.assert_response(ResponseCode.OK)
        self.assertTrue(self.command_handler._started)

        await self.command_handler.handle_command(command=Command.STOP)
        self.assert_response(ResponseCode.OK)
        # Give time to the telemetry_task to get cancelled.
        await asyncio.sleep(0.5)
        self.assertFalse(self.command_handler._started)

    async def test_get_telemetrey(self):
        await self.command_handler.handle_command(
            command=Command.CONFIGURE, configuration=self.configuration
        )
        self.assert_response(ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)
        await self.command_handler.handle_command(command=Command.START)
        self.assert_response(ResponseCode.OK)
        self.assertTrue(self.command_handler._started)

        # Give some time to the mock sensor to produce data
        while len(self.responses) < len(self.device_configs):
            await asyncio.sleep(0.5)

        devices_names_checked = set()
        while len(devices_names_checked) != len(self.device_configs):
            response = self.responses.pop()
            telemetry = response[Key.TELEMETRY]
            device_name = telemetry[0]
            devices_names_checked.add(device_name)
            config = self.device_configs[device_name]
            for i in range(3, config.channels + 3):
                assert (
                    MockTemperatureSensor.MIN_TEMP
                    <= telemetry[i]
                    <= MockTemperatureSensor.MAX_TEMP
                )

        await self.command_handler.handle_command(command=Command.STOP)
        self.assert_response(ResponseCode.OK)
        # Give time to the telemetry_task to get cancelled.
        await asyncio.sleep(0.5)
        self.assertFalse(self.command_handler._started)
