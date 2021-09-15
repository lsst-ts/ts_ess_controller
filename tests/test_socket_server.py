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
import json
import logging
import typing
import unittest

from lsst.ts import tcpip
from lsst.ts.ess import common, controller
from base_mock_test_case import BaseMockTestCase

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

TIMEOUT = 5
"""Standard timeout in seconds."""


class SocketServerTestCase(BaseMockTestCase):
    async def asyncSetUp(self) -> None:
        self.ctrl = None
        self.writer = None
        self.mock_ctrl = None
        self.srv = common.SocketServer(
            name="EssSensorsServer", host="0.0.0.0", port=0, simulation_mode=1
        )
        command_handler = controller.CommandHandler(
            callback=self.srv.write, simulation_mode=1
        )
        self.srv.set_command_handler(command_handler)

        self.log = logging.getLogger(type(self).__name__)

        await self.srv.start_task
        self.assertTrue(self.srv.server.is_serving())
        self.reader, self.writer = await asyncio.open_connection(
            host=tcpip.LOCAL_HOST, port=self.srv.port
        )

    async def asyncTearDown(self) -> None:
        await self.srv.disconnect()
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        await self.srv.exit()

    async def read(self) -> typing.Dict[str, typing.Any]:
        """Read a string from the reader and unmarshal it

        Returns
        -------
        data : `dict`
            A dictionary with objects representing the string read.
        """
        read_bytes = await asyncio.wait_for(
            self.reader.readuntil(tcpip.TERMINATOR), timeout=TIMEOUT
        )
        data = json.loads(read_bytes.decode())
        return data

    async def write(self, **data: typing.Dict[str, typing.Any]) -> None:
        """Write the data appended with a tcpip.TERMINATOR string.

        Parameters
        ----------
        data:
            The data to write.
        """
        st = json.dumps({**data})
        assert self.writer is not None
        self.writer.write(st.encode() + tcpip.TERMINATOR)
        await self.writer.drain()

    async def test_disconnect(self) -> None:
        self.assertTrue(self.srv.connected)
        await self.write(command=common.Command.DISCONNECT, parameters={})
        # Give time to the socket server to clean up internal state and exit.
        await asyncio.sleep(0.5)
        self.assertFalse(self.srv.connected)

    async def test_exit(self) -> None:
        self.assertTrue(self.srv.connected)
        await self.write(command=common.Command.EXIT, parameters={})
        # Give time to the socket server to clean up internal state and exit.
        await asyncio.sleep(0.5)
        self.assertFalse(self.srv.connected)

    async def check_server_test(self) -> None:
        """Test a full command sequence of the SocketServer.

        The sequence is
            - configure
            - start
            - read telemetry
            - stop
            - disconnect
            - exit
        """
        configuration = {
            common.Key.DEVICES: [
                {
                    common.Key.NAME: self.name,
                    common.Key.CHANNELS: self.num_channels,
                    common.Key.DEVICE_TYPE: common.DeviceType.FTDI,
                    common.Key.FTDI_ID: "ABC",
                    common.Key.SENSOR_TYPE: common.SensorType.TEMPERATURE,
                }
            ]
        }
        await self.write(
            command=common.Command.CONFIGURE,
            parameters={common.Key.CONFIGURATION: configuration},
        )
        data = await self.read()
        self.assertEqual(common.ResponseCode.OK, data[common.Key.RESPONSE])
        await self.write(command=common.Command.START, parameters={})
        data = await self.read()
        self.assertEqual(common.ResponseCode.OK, data[common.Key.RESPONSE])

        # Make sure that the mock sensor outputs data for a disconnected
        # channel.
        self.srv.command_handler._devices[
            0
        ]._disconnected_channel = self.disconnected_channel

        # Make sure that the mock sensor outputs truncated data.
        self.srv.command_handler._devices[0]._missed_channels = self.missed_channels

        # Make sure that the mock sensor is in error state.
        self.srv.command_handler._devices[0]._in_error_state = self.in_error_state

        self.reply = await self.read()
        reply_to_check = self.reply[common.Key.TELEMETRY]
        self.check_temperature_reply(reply_to_check)

        # Reset self.missed_channels and read again. The data should not be
        # truncated anymore.
        self.missed_channels = 0

        self.reply = await self.read()
        reply_to_check = self.reply[common.Key.TELEMETRY]
        self.check_temperature_reply(reply_to_check)

        await self.write(command=common.Command.STOP, parameters={})
        data = await self.read()
        self.assertEqual(common.ResponseCode.OK, data[common.Key.RESPONSE])
        await self.write(command=common.Command.DISCONNECT, parameters={})
        await self.write(command=common.Command.EXIT, parameters={})

    async def test_full_command_sequence(self) -> None:
        """Test the SocketServer with a nominal configuration, i.e. no
        disconnected channels and no truncated data.
        """
        self.name = "Test1"
        self.num_channels = 1
        self.disconnected_channel = None
        self.missed_channels = 0
        self.in_error_state = False
        await self.check_server_test()

    async def test_full_command_sequence_with_disconnected_channel(self) -> None:
        """Test the SocketServer with one disconnected channel and no truncated
        data.
        """
        self.name = "Test1"
        self.num_channels = 4
        self.disconnected_channel = 1
        self.missed_channels = 0
        self.in_error_state = False
        await self.check_server_test()

    async def test_full_command_sequence_with_truncated_output(self) -> None:
        """Test the SocketServer with no disconnected channels and truncated
        data for two channels.
        """
        self.name = "Test1"
        self.num_channels = 4
        self.disconnected_channel = None
        self.missed_channels = 2
        self.in_error_state = False
        await self.check_server_test()

    async def test_full_command_sequence_in_error_state(self) -> None:
        """Test the SocketServer with a sensor in error state, meaning it will
        only output empty strings.
        """
        self.name = "Test1"
        self.num_channels = 4
        self.disconnected_channel = None
        self.missed_channels = 0
        self.in_error_state = True
        await self.check_server_test()
