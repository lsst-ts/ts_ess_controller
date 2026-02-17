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

__all__ = ["VcpFtdi"]

import asyncio
import datetime
import logging
import re
from typing import Callable

from pylibftdi import Device

from lsst.ts.ess import common

from .mock_serial import MockSerial

# Reconnect sleep time [seconds].
RECONNECT_SLEEP = 60.0

# Read timeout [sec].
READ_TIMEOUT = 10.0


class VcpFtdi(common.device.BaseDevice):
    """USB Virtual Communications Port (VCP) for FTDI device.

    Parameters
    ----------
    name : `str`
        The name of the device.
    device_id : `str`
        The hardware device ID to connect to. This needs to be an FTDI device
        identifier.
    sensor : `BaseSensor`
        The sensor that produces the telemetry.
    baud_rate : `int`
        The baud rate of the sensor.
    callback_func : `Callable`
        Callback function to receive the telemetry.
    log : `logging.Logger`
        The logger to create a child logger for.
    use_mock_device : `bool`
        Use the mock device or not. Defaults to False.
    read_generates_error : `bool`
        Does reading the divice generate an error or not. Defaults to False.
    generate_timeout : `bool`
        Expect a timeout.
    """

    reconnect_sleep = RECONNECT_SLEEP
    read_timeout = READ_TIMEOUT

    def __init__(
        self,
        name: str,
        device_id: str,
        sensor: common.sensor.BaseSensor,
        baud_rate: int,
        callback_func: Callable,
        log: logging.Logger,
        use_mock_device: bool = False,
        read_generates_error: bool = False,
        generate_timeout: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            device_id=device_id,
            sensor=sensor,
            baud_rate=baud_rate,
            callback_func=callback_func,
            log=log,
        )
        if use_mock_device:
            self.vcp = MockSerial(
                read_generates_error=read_generates_error,
                encode_reply=False,
                generate_timeout=generate_timeout,
            )
        else:
            self.vcp = Device(
                self.device_id,
                mode="t",
                encoding="ASCII",
                lazy_open=True,
                auto_detach=False,
            )

        # Build a regular expression to use when checking if the sensor has
        # sent the end of a telemetry string. Occasionally an additional
        # NULL character may show up so we need to check for that.
        enhanced_terminator = ".?".join(self.sensor.terminator)
        self.enhanced_terminator_regex = re.compile(enhanced_terminator)
        self.terminator_regex = re.compile("^.*" + enhanced_terminator + "$")

        # Keep track of the previous time a readline was performed.
        self.previous_readline_time: datetime.datetime | None = None

    async def basic_open(self) -> None:
        """Open the Sensor Device.

        Opens the virtual communications port and flushes the device input and
        output buffers.

        Raises
        ------
        IOError if virtual communications port fails to open.
        """
        self.vcp.open()
        # Setting the baud rate requires the vcp Device to have set up a
        # context, which only happens when open() is called. That's why this
        # next line *needs* to be called after calling open().
        self.vcp.baudrate = self.baud_rate
        if not self.vcp.closed:
            self.log.info(f"FTDI device {self.device_id} open.")
            self.vcp.flush()
        else:
            self.log.error(f"FTDI device {self.device_id} open failed.")
            raise IOError(f"{self.name}: Failed to open the FTDI device.")

    async def readline(self) -> str:
        """Read a line of telemetry from the device.

        Returns
        -------
        line : `str`
            Line read from the device. Includes terminator string if there is
            one. May be returned empty if nothing was received or partial if
            the readline was started during device reception.
        """
        line: str = ""
        # get running loop to run blocking tasks
        loop = asyncio.get_running_loop()

        try:
            async with asyncio.timeout(self.read_timeout):
                # All sensor telemetry lines end either in \r\n or in \n\r so
                # this next while condition should be safe.
                while not ("\r" in line and "\n" in line):
                    ch = await loop.run_in_executor(None, self.vcp.read, 1)
                    self.log.debug(f"Read {self.name} {ch=!r}.")
                    assert isinstance(ch, str)
                    line += ch
        except TimeoutError:
            self.log.exception(f"Timeout reading {self.name}. So far {line=!r}.")
            raise
        line = self.enhanced_terminator_regex.sub(self.sensor.terminator, line)

        now = datetime.datetime.now(datetime.UTC)
        if self.previous_readline_time is not None:
            interval = (now - self.previous_readline_time).total_seconds()
            if interval > self.read_timeout:
                self.log.warning(f"Previous {self.name} readline was {interval} seconds ago.")
        self.previous_readline_time = now

        self.log.debug(f"Returning {self.name} {line=}")
        return line

    async def handle_readline_exception(self, exception: BaseException) -> None:
        """Handle any exception that happened in the `readline` method.

        The default is to log and ignore but subclasses may override this
        method to customize the behavior.

        Parameters
        ----------
        exception : `BaseException`
            The exception to handle.
        """
        if not isinstance(exception, asyncio.CancelledError):
            self.log.exception(
                f"Exception reading device {self.name}. "
                f"Trying to reconnect after {self.reconnect_sleep} seconds."
            )
            await self.basic_close()
            await asyncio.sleep(self.reconnect_sleep)
            raise

    async def basic_close(self) -> None:
        """Close the Sensor Device.

        Raises
        ------
        IOError if virtual communications port fails to close.
        """
        self.vcp.close()
        if self.vcp.closed:
            self.log.info(f"FTDI device {self.device_id} closed.")
        else:
            self.log.info(f"FTDI device {self.device_id} close failed.")
            raise IOError(f"VcpFtdi:{self.name}: Failed to close the FTDI device.")
