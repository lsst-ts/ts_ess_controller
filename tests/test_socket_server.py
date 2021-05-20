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
import json
import logging
import unittest

from lsst.ts.envsensors import SocketServer, ResponseCode
from lsst.ts.envsensors.mock.mock_temperature_sensor import MockTemperatureSensor

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

TIMEOUT = 5
"""Standard timeout in seconds."""


class SocketServerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.ctrl = None
        self.writer = None
        port = 0
        self.mock_ctrl = None
        self.data = None
        self.srv = SocketServer(port=port, simulation_mode=1)

        self.log = logging.getLogger(type(self).__name__)

        self.assertFalse(self.srv._started)
        asyncio.create_task(self.srv.start())
        await asyncio.sleep(0.5)
        self.assertTrue(self.srv._started)
        # Request the assigned port from the mock controller.
        port = self.srv.port

        rw_coro = asyncio.open_connection(host="127.0.0.1", port=port)
        self.reader, self.writer = await asyncio.wait_for(rw_coro, timeout=TIMEOUT)

    async def asyncTearDown(self):
        if self.srv._started:
            await self.srv.exit()
        if self.writer:
            self.writer.close()

    async def read(self):
        """Utility function to read a string from the reader and unmarshal it

        Returns
        -------
        data : `dict`
            A dictionary with objects representing the string read.
        """
        read_bytes = await asyncio.wait_for(
            self.reader.readuntil(b"\r\n"), timeout=TIMEOUT
        )
        data = json.loads(read_bytes.decode())
        return data

    async def write(self, **data):
        """Write the data appended with a newline character.

        Parameters
        ----------
        data:
            The data to write.
        """
        st = json.dumps({**data})
        self.writer.write(st.encode() + b"\r\n")
        self.log.debug(st)
        await self.writer.drain()

    async def test_exit(self):
        await self.write(command="exit", parameters={})
        # Give time to the socket server to clean up internal state and exit.
        await asyncio.sleep(0.5)
        self.assertFalse(self.srv._started)

    async def test_full_command_sequence(self):
        name = "Test1"
        channels = 1
        configuration = {"devices": [{"name": name, "channels": channels}]}
        await self.write(
            command="configure", parameters={"configuration": configuration}
        )
        self.data = await self.read()
        self.assertEqual(ResponseCode.OK, self.data["response"])
        await self.write(command="start", parameters={})
        self.data = await self.read()
        self.assertEqual(ResponseCode.OK, self.data["response"])
        self.data = await self.read()
        telemetry = self.data["telemetry"]
        self.assertEqual(telemetry[0], name)
        self.assertEqual(telemetry[2], "OK")
        assert (
            MockTemperatureSensor.MIN_TEMP
            <= telemetry[3]
            <= MockTemperatureSensor.MAX_TEMP
        )

        await self.write(command="stop", parameters={})
        self.data = await self.read()
        self.assertEqual(ResponseCode.OK, self.data["response"])
        await self.write(command="exit", parameters={})
        # Give time to the socket server to clean up internal state and exit.
        await asyncio.sleep(0.5)
        self.assertFalse(self.srv._started)
