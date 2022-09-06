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

import asyncio
import logging
import typing
import unittest

from lsst.ts.ess import common, controller
from lsst.ts.ess.common.test_utils import MockTestTools

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class CommandHandlerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.command_handler = controller.CommandHandler(
            callback=self.callback, simulation_mode=1
        )
        assert self.command_handler.configuration is None

        # Despite simulation_mode being set to 1, full fledged configuration is
        # needed because of the configuration validation. All device
        # configuration is ignored but the sensor type is not. The main
        # objective is to test multiple sensors at the same time.
        device_config_01 = common.DeviceConfig(
            name="Test01",
            num_channels=4,
            dev_type=common.DeviceType.FTDI,
            dev_id="ABC",
            sens_type=common.SensorType.TEMPERATURE,
            baud_rate=19200,
            location="Test1",
        )
        device_config_02 = common.DeviceConfig(
            name="Test02",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABC",
            sens_type=common.SensorType.HX85A,
            baud_rate=19200,
            location="Test2",
        )
        device_config_03 = common.DeviceConfig(
            name="Test03",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABC",
            sens_type=common.SensorType.HX85BA,
            baud_rate=19200,
            location="Test3",
        )
        device_config_04 = common.DeviceConfig(
            name="Test04",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABC",
            sens_type=common.SensorType.CSAT3B,
            baud_rate=115200,
            location="Test4",
        )
        self.configuration = {
            common.Key.DEVICES: [
                device_config_01.as_dict(),
                device_config_02.as_dict(),
                device_config_03.as_dict(),
                device_config_04.as_dict(),
            ]
        }
        self.device_configs = {
            device_config_01.name: device_config_01,
            device_config_02.name: device_config_02,
            device_config_03.name: device_config_03,
            device_config_04.name: device_config_04,
        }
        self.responses: typing.List[typing.List[typing.Union[str, float]]] = []

    async def callback(self, response: typing.List[typing.Union[str, float]]) -> None:
        self.responses.append(response)

    def assert_response(self, response_code: str) -> None:
        response = self.responses.pop()
        assert response[common.Key.RESPONSE] == response_code

    async def test_configure(self) -> None:
        """Test the configuration validation of the CommandHandler."""

        # Test with the configuration as set in asyncSetUp, which is a good
        # configuration.
        await self.command_handler.handle_command(
            command=common.Command.CONFIGURE, configuration=self.configuration
        )
        self.assert_response(common.ResponseCode.OK)
        assert self.configuration == self.command_handler.configuration
        # Send the same configuration again which should lead to an error.
        await self.command_handler.handle_command(
            command=common.Command.CONFIGURE, configuration=self.configuration
        )
        self.assert_response(common.ResponseCode.ALREADY_STARTED)
        # Make sure to stop so a new config command can be sent.
        await self.command_handler.stop_sending_telemetry()
        assert self.command_handler._started is False
        # Send the same configuration again which should now be OK.
        await self.command_handler.handle_command(
            command=common.Command.CONFIGURE, configuration=self.configuration
        )
        self.assert_response(common.ResponseCode.OK)
        # Make sure to stop so a new config command can be sent.
        await self.command_handler.stop_sending_telemetry()
        assert self.command_handler._started is False

        # The value for common.Key.DEVICES may not be empty.
        bad_configuration: typing.Dict[str, typing.Any] = {common.Key.DEVICES: []}
        await self.command_handler.handle_command(
            command=common.Command.CONFIGURE, configuration=bad_configuration
        )
        self.assert_response(common.ResponseCode.INVALID_CONFIGURATION)

        # A configuration with several errors that will get tested one by one.
        bad_items = [
            {
                # The mandatory keys common.Key.CHANNELS,
                # common.Key.DEVICE_TYPE and KEY.SENSOR_TYPE are missing.
                common.Key.NAME: "Test1",
            },
            {
                # The mandatory keys common.Key.DEVICE_TYPE and
                # common.Key.SENSOR_TYPE are missing.
                common.Key.NAME: "Test1",
                common.Key.CHANNELS: 4,
            },
            {
                # The mandatory key common.Key.SENSOR_TYPE is missing.
                common.Key.NAME: "Test1",
                common.Key.CHANNELS: 4,
                common.Key.DEVICE_TYPE: common.DeviceType.FTDI,
            },
            {
                # For common.DeviceType.FTDI the key
                # common.Key.FTDI_ID is mandatory.
                common.Key.NAME: "Test1",
                common.Key.CHANNELS: 4,
                common.Key.DEVICE_TYPE: common.DeviceType.FTDI,
                "id": "ABC",
                common.Key.SENSOR_TYPE: common.SensorType.TEMPERATURE,
            },
            {
                # For common.DeviceType.SERIAL the key
                # common.Key.SERIAL_PORT is mandatory.
                common.Key.NAME: "Test1",
                common.Key.CHANNELS: 4,
                common.Key.DEVICE_TYPE: common.DeviceType.SERIAL,
                "port": "ABC",
                common.Key.SENSOR_TYPE: common.SensorType.TEMPERATURE,
            },
            {
                # Wrong value for common.Key.SENSOR_TYPE.
                common.Key.NAME: "Test1",
                common.Key.CHANNELS: 4,
                common.Key.DEVICE_TYPE: common.DeviceType.SERIAL,
                common.Key.SERIAL_PORT: "ABC",
                common.Key.SENSOR_TYPE: "Temp",
            },
        ]
        for bad_item in bad_items:
            bad_configuration = {common.Key.DEVICES: [bad_item]}
            await self.command_handler.handle_command(
                command=common.Command.CONFIGURE, configuration=bad_configuration
            )
            self.assert_response(common.ResponseCode.INVALID_CONFIGURATION)

    async def test_start_and_stop(self) -> None:
        """Test handling of the start command."""
        assert self.command_handler.configuration is None
        assert self.command_handler._started is False

        await self.command_handler.handle_command(
            command=common.Command.CONFIGURE, configuration=self.configuration
        )
        self.assert_response(common.ResponseCode.OK)
        assert self.command_handler.configuration is not None
        assert self.configuration == self.command_handler.configuration
        assert self.command_handler._started is True

        await self.command_handler.stop_sending_telemetry()
        assert self.command_handler._started is False

    async def test_get_telemetry(self) -> None:
        """Test handling of telemetry."""
        mtt = MockTestTools()
        await self.command_handler.handle_command(
            command=common.Command.CONFIGURE, configuration=self.configuration
        )
        self.assert_response(common.ResponseCode.OK)
        assert self.configuration == self.command_handler.configuration
        assert self.command_handler._started is True

        # Give some time to the mock sensor to produce data
        while len(self.responses) < len(self.device_configs):
            await asyncio.sleep(0.5)

        devices_names_checked: typing.Set[str] = set()
        while len(devices_names_checked) != len(self.device_configs):
            reply = self.responses.pop()
            name = reply[common.Key.TELEMETRY][common.Key.NAME]
            devices_names_checked.add(name)
            device_config = self.device_configs[name]
            reply_to_check = reply[common.Key.TELEMETRY]
            if device_config.sens_type == common.SensorType.TEMPERATURE:
                num_channels = device_config.num_channels
                mtt.check_temperature_reply(
                    reply=reply_to_check, name=name, num_channels=num_channels
                )
            elif device_config.sens_type == common.SensorType.HX85A:
                mtt.check_hx85a_reply(reply=reply_to_check, name=name)
            elif device_config.sens_type == common.SensorType.HX85BA:
                mtt.check_hx85ba_reply(reply=reply_to_check, name=name)
            elif device_config.sens_type == common.SensorType.CSAT3B:
                mtt.check_csat3b_reply(reply=reply_to_check, name=name)
            else:
                raise ValueError(
                    f"Unsupported sensor type {device_config.sens_type} encountered."
                )

        await self.command_handler.stop_sending_telemetry()
        assert self.command_handler._started is False
