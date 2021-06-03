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
    CommandHandler,
    ResponseCode,
    CMD_CONFIGURE,
    CMD_START,
    CMD_STOP,
    KEY_CHANNELS,
    KEY_DEVICES,
    KEY_FTDI_ID,
    KEY_NAME,
    KEY_RESPONSE,
    KEY_SERIAL_PORT,
    KEY_TELEMETRY,
    KEY_TYPE,
    VAL_FTDI,
    VAL_SERIAL,
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
            name="Test01", channels=4, dev_type=VAL_FTDI, dev_id="ABC"
        )
        device_config_02 = DeviceConfig(
            name="Test02", channels=6, dev_type=VAL_FTDI, dev_id="ABC"
        )
        device_config_03 = DeviceConfig(
            name="Test03", channels=2, dev_type=VAL_FTDI, dev_id="ABC"
        )
        self.configuration = {
            KEY_DEVICES: [
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

    async def test_validate_configuration(self):
        configuration = {
            KEY_DEVICES: [
                {
                    KEY_NAME: "Test1",
                    KEY_CHANNELS: 4,
                    KEY_TYPE: VAL_FTDI,
                    KEY_FTDI_ID: "ABC",
                },
                {
                    KEY_NAME: "Test1",
                    KEY_CHANNELS: 4,
                    KEY_TYPE: VAL_SERIAL,
                    KEY_SERIAL_PORT: "ABC",
                },
            ]
        }
        self.assertTrue(
            self.command_handler._validate_configuration(configuration=configuration)
        )
        configuration = {
            KEY_DEVICES: [
                {
                    KEY_NAME: "Test1",
                },
                {
                    KEY_NAME: "Test1",
                    KEY_CHANNELS: 4,
                },
                {
                    KEY_NAME: "Test1",
                    KEY_CHANNELS: 4,
                    KEY_TYPE: VAL_FTDI,
                    "id": "ABC",
                },
                {
                    KEY_NAME: "Test1",
                    KEY_CHANNELS: 4,
                    KEY_TYPE: VAL_SERIAL,
                    "port": "ABC",
                },
            ]
        }
        self.assertFalse(
            self.command_handler._validate_configuration(configuration=configuration)
        )
        configuration = {KEY_DEVICES: []}
        self.assertFalse(
            self.command_handler._validate_configuration(configuration=configuration)
        )
        configuration = {
            "KEY_DEVICES": [
                {
                    KEY_NAME: "Test1",
                },
                {
                    KEY_NAME: "Test1",
                    KEY_CHANNELS: 4,
                },
                {
                    KEY_NAME: "Test1",
                    KEY_CHANNELS: 4,
                    KEY_TYPE: VAL_FTDI,
                    "id": "ABC",
                },
                {
                    KEY_NAME: "Test1",
                    KEY_CHANNELS: 4,
                    KEY_TYPE: VAL_SERIAL,
                    "port": "ABC",
                },
            ]
        }
        self.assertFalse(
            self.command_handler._validate_configuration(configuration=configuration)
        )

    def validate_response(self, response_code):
        response = self.responses.pop()
        self.assertEqual(response[KEY_RESPONSE], response_code)

    async def test_configure(self):
        await self.command_handler.handle_command(
            command=CMD_CONFIGURE, configuration=self.configuration
        )
        self.validate_response(ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)

        configuration = {
            "KEY_DEVICES": [
                {
                    KEY_NAME: "Test1",
                },
                {
                    KEY_NAME: "Test1",
                    KEY_CHANNELS: 4,
                },
                {
                    KEY_NAME: "Test1",
                    KEY_CHANNELS: 4,
                    KEY_TYPE: VAL_FTDI,
                    "id": "ABC",
                },
                {
                    KEY_NAME: "Test1",
                    KEY_CHANNELS: 4,
                    KEY_TYPE: VAL_SERIAL,
                    "port": "ABC",
                },
            ]
        }
        await self.command_handler.handle_command(
            command=CMD_CONFIGURE, configuration=configuration
        )
        self.validate_response(ResponseCode.INVALID_CONFIGURATION)

    async def test_start(self):
        await self.command_handler.handle_command(command=CMD_START)
        self.validate_response(ResponseCode.NOT_CONFIGURED)
        self.assertIsNone(self.command_handler._configuration)
        self.assertFalse(self.command_handler._started)

        await self.command_handler.handle_command(
            command=CMD_CONFIGURE, configuration=self.configuration
        )
        self.validate_response(ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)
        await self.command_handler.handle_command(command=CMD_START)
        self.validate_response(ResponseCode.OK)
        self.assertTrue(self.command_handler._started)

    async def test_stop(self):
        await self.command_handler.handle_command(command=CMD_STOP)
        self.validate_response(ResponseCode.NOT_STARTED)
        self.assertIsNone(self.command_handler._configuration)
        self.assertFalse(self.command_handler._started)

        await self.command_handler.handle_command(
            command=CMD_CONFIGURE, configuration=self.configuration
        )
        self.validate_response(ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)
        await self.command_handler.handle_command(command=CMD_START)
        self.validate_response(ResponseCode.OK)
        self.assertTrue(self.command_handler._started)

        await self.command_handler.handle_command(command=CMD_STOP)
        self.validate_response(ResponseCode.OK)
        # Give time to the telemetry_task to get cancelled.
        await asyncio.sleep(0.5)
        self.assertFalse(self.command_handler._started)

    async def test_get_telemetrey(self):
        await self.command_handler.handle_command(
            command=CMD_CONFIGURE, configuration=self.configuration
        )
        self.validate_response(ResponseCode.OK)
        self.assertDictEqual(self.configuration, self.command_handler._configuration)
        await self.command_handler.handle_command(command=CMD_START)
        self.validate_response(ResponseCode.OK)
        self.assertTrue(self.command_handler._started)

        # Give some time to the mock sensor to produce data
        while len(self.responses) < len(self.device_configs):
            await asyncio.sleep(0.5)

        devices_names_checked = set()
        while len(devices_names_checked) != len(self.device_configs):
            response = self.responses.pop()
            telemetry = response[KEY_TELEMETRY]
            device_name = telemetry[0]
            devices_names_checked.add(device_name)
            config = self.device_configs[device_name]
            for i in range(3, config.channels + 3):
                assert (
                    MockTemperatureSensor.MIN_TEMP
                    <= telemetry[i]
                    <= MockTemperatureSensor.MAX_TEMP
                )

        await self.command_handler.handle_command(command=CMD_STOP)
        self.validate_response(ResponseCode.OK)
        # Give time to the telemetry_task to get cancelled.
        await asyncio.sleep(0.5)
        self.assertFalse(self.command_handler._started)
