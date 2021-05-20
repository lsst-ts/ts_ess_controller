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

__all__ = ["SocketServer"]

import asyncio
import json
import logging

from .command_handler import CommandHandler


class SocketServer:
    """A server for exchanging messages that talks over TCP/IP.

    Upon initiation a socket server is set up which waits for incoming
    commands. When an exit command is received, the socket server will exit.
    All other commands are dispatched to the command handler.

    Parameters
    ----------
    port : int
        The port number.
    simulation_mode : `int`, optional
        Simulation mode. The default is 0: do not simulate.
    """

    valid_simulation_modes = (0, 1)

    def __init__(self, port, simulation_mode=0):
        self.port = port
        if simulation_mode not in self.valid_simulation_modes:
            raise ValueError(
                f"simulation_mode={simulation_mode} "
                f"not in valid_simulation_modes={self.valid_simulation_modes}"
            )

        self.simulation_mode = simulation_mode

        self._server = None
        self._writer = None
        self._reader = None
        self._started = False
        self.log = logging.getLogger(type(self).__name__)

        self.command_handler = CommandHandler(
            callback=self.write, simulation_mode=self.simulation_mode
        )

    async def start(self):
        """Start the TCP/IP server.

        Start the command loop and make sure to keep running when instructed to
        do so.
        """
        self.log.info("Start called")
        self._started = True
        self._server = await asyncio.start_server(
            self.read_loop, host="127.0.0.1", port=self.port
        )

        # Request the assigned port from the server so the code starting the
        # mock controller can use it to connect.
        if self.port == 0:
            self.port = self._server.sockets[0].getsockname()[1]

        await self._server.serve_forever()

    async def write(self, data):
        """Write the data appended with a newline character.

        The data are encoded via JSON and then passed on to the StreamWriter
        associated with the socket.

        Parameters
        ----------
        data:
            The data to write.
        """
        self.log.debug(f"Writing data {data}")
        st = json.dumps({**data})
        self.log.debug(st)
        if self._writer:
            self._writer.write(st.encode() + b"\r\n")
            await self._writer.drain()
        self.log.debug("Done")

    async def read_loop(self, reader, writer):
        """Read commands and output replies.

        Parameters
        ----------
        reader: stream reader
            The stream reader to read from.
        writer: stream writer
            The stream writer to write to.
        """
        self.log.info("The read_loop begins")
        self._writer = writer
        self._reader = reader

        while self._started:
            self.log.debug("Waiting for next incoming message.")
            try:
                line = await reader.readuntil(b"\r\n")
                line = line.decode().strip()
                self.log.debug(f"Read command line: {line!r}")
                items = json.loads(line)
                cmd = items["command"]
                kwargs = items["parameters"]
                if cmd == "exit":
                    await self.exit()
                else:
                    await self.command_handler.handle_command(cmd, **kwargs)

            except asyncio.IncompleteReadError:
                return

    async def exit(self):
        """Stop the TCP/IP server."""
        self._started = False

        if self._server is None:
            return

        self.log.info("Closing server")
        server = self._server
        self._server = None
        server.close()

        self.log.info("Closing writer")
        writer = self._writer
        self._writer = None
        writer.close()

        self.log.info("Closing reader")
        self._reader = None
        self.log.info("Done closing")
