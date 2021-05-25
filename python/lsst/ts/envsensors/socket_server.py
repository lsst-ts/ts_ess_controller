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
from lsst.ts import tcpip


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

    def __init__(self, port: int, simulation_mode: int = 0) -> None:
        self.host: str = "0.0.0.0"  # always read on all interfaces
        self.port: int = port
        if simulation_mode not in self.valid_simulation_modes:
            raise ValueError(
                f"simulation_mode={simulation_mode} "
                f"not in valid_simulation_modes={self.valid_simulation_modes}"
            )

        self.simulation_mode = simulation_mode

        self._server: tcpip.OneClientServer = None
        self.read_loop_task: asyncio.Future = asyncio.Future()
        self.log: logging.Logger = logging.getLogger(type(self).__name__)

        self.command_handler: CommandHandler = CommandHandler(
            callback=self.write, simulation_mode=self.simulation_mode
        )

    async def start(self) -> None:
        """Start the TCP/IP server.

        Start the command loop and make sure to keep running when instructed to
        do so.

        Parameters
        ----------
        keep_running : bool
            Used for command line testing and should generally be left to
            False.
        """
        self.log.info("Start called")
        self._server = tcpip.OneClientServer(
            host=self.host,
            port=self.port,
            name=self.log.name,
            log=self.log,
            connect_callback=self.connected_callback,
        )
        await self._server.start_task

        # Request the assigned port from the server so the code starting the
        # mock controller can use it to connect.
        if self.port == 0:
            self.port = self._server.port

    def connected_callback(self, server: tcpip.OneClientServer) -> None:
        """A client has connected or disconnected."""
        if not server.connected:
            self.log.info("Client disconnected.")
        else:
            self.log.info("Client connected.")
        self.read_loop_task.cancel()
        if server.connected:
            self.log.info("Starting a new read loop.")
            self.read_loop_task = asyncio.create_task(self.read_loop())

    async def write(self, data: dict) -> None:
        """Write the data appended with a newline character.

        The data are encoded via JSON and then passed on to the StreamWriter
        associated with the socket.

        Parameters
        ----------
        data: `dict`
            The data to write.
        """
        self.log.debug(f"Writing data {data}")
        st = json.dumps({**data})
        self.log.debug(st)
        if self._server.writer:
            self._server.writer.write(st.encode() + tcpip.TERMINATOR)
            await self._server.writer.drain()
        self.log.debug("Done")

    async def read_loop(self) -> None:
        """Read commands and output replies."""
        try:
            self.log.info(f"The read_loop begins connected? {self._server.connected}")
            while self._server and self._server.connected:
                self.log.debug("Waiting for next incoming message.")
                try:
                    line = await self._server.reader.readuntil(tcpip.TERMINATOR)
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
                    pass

        except Exception:
            self.log.exception("read_loop failed")

    async def exit(self) -> None:
        """Stop the TCP/IP server."""
        if self._server is None:
            return

        if self._server.writer:
            self.log.info("Closing writer")
            await tcpip.close_stream_writer(self._server.writer)

        self.log.info("Closing server")
        await self._server.close()

        self.log.info("Done closing")
