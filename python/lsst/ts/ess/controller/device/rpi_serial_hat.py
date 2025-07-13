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

__all__ = ["RpiSerialHat"]

import asyncio
import logging
import re
from typing import Callable

from lsst.ts.ess import common
from serial import Serial, SerialException

from .mock_serial import MockSerial

# Reconnect sleep time [seconds].
RECONNECT_SLEEP = 60.0

# Read timeout [sec].
READ_TIMEOUT = 10.0


class RpiSerialHat(common.device.BaseDevice):
    """Raspberry Pi serial device connected to the hat.

    Parameters
    ----------
    name : `str`
        The name of the device.
    device_id : `str`
        The hardware device ID to connect to. This needs to be a physical ID
        (e.g. /dev/ttyUSB0).
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
    """

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
    ) -> None:
        super().__init__(
            name=name,
            device_id=device_id,
            sensor=sensor,
            baud_rate=baud_rate,
            callback_func=callback_func,
            log=log,
        )
        try:
            if use_mock_device:
                self.ser = MockSerial(
                    read_generates_error=read_generates_error, encode_reply=True
                )
            else:
                self.ser = Serial(port=device_id, baudrate=self.baud_rate)
        except SerialException as e:
            self.log.exception(f"{e!r}")
            # Unrecoverable error, so propagate error
            raise

        # Keep track of whether the first telemetry from the sensor have been
        # read or not. If not then decoding errors will be ignored.
        self.first_telemetry_read = False

        # Build a regular expression to use when checking if the sensor has
        # sent the end of a telemetry string. Occasionally an additional
        # NULL character may show up so we need to check for that.
        enhanced_terminator = ".?".join(self.sensor.terminator)
        self.enhanced_terminator_regex = re.compile(enhanced_terminator)
        self.terminator_regex = re.compile("^.*" + enhanced_terminator + "$")

    async def basic_open(self) -> None:
        """Open and configure serial port.
        Open the serial communications port and set BAUD.

        Raises
        ------
        IOError if serial communications port fails to open.
        """
        if not self.ser.is_open:
            try:
                self.ser.open()
                self.log.info(f"Serial port {self.device_id} opened.")
            except SerialException as e:
                self.log.exception(f"Serial port {self.device_id} open failed.")
                raise e
        else:
            self.log.info(f"Serial port {self.device_id} already open.")

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
        loop = asyncio.get_running_loop()

        async with asyncio.timeout(READ_TIMEOUT):
            # All sensor telemetry lines end either in \r\n or in \n\r so this
            # next while condition should be safe.
            while not ("\r" in line and "\n" in line):
                b_ch = await loop.run_in_executor(None, self.ser.read, 1)
                assert isinstance(b_ch, bytes)
                ch = b_ch.decode(encoding=self.sensor.charset)
                self.log.info(f"Read {self.name} {ch=!r}.")
                line += ch
        line = self.enhanced_terminator_regex.sub(self.sensor.terminator, line)
        self.log.info(f"Returning {self.name} {line=}")
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
                f"Trying to reconnect after {RECONNECT_SLEEP} seconds."
            )
            self.is_open = False
            await asyncio.sleep(RECONNECT_SLEEP)

    async def basic_close(self) -> None:
        """Close the Sensor Device.

        Raises
        ------
        IOError if virtual communications port fails to close.
        """
        if self.ser.is_open:
            self.ser.close()
            self.log.info(f"Serial port {self.device_id} closed.")
        else:
            self.log.info(f"Serial port {self.device_id} already closed.")
