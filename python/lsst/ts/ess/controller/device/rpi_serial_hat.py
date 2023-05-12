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
from typing import Callable

from aioserial import AioSerial, SerialException
from lsst.ts.ess import common

# Read tiumeout [seconds].
READ_TIMEOUT = 5.0


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
    """

    def __init__(
        self,
        name: str,
        device_id: str,
        sensor: common.sensor.BaseSensor,
        baud_rate: int,
        callback_func: Callable,
        log: logging.Logger,
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
            self.ser = AioSerial(port=device_id, baudrate=self.baud_rate)
            self.log.debug(f"Port: {self.ser.port}")
        except SerialException as e:
            self.log.exception(f"{e!r}")
            # Unrecoverable error, so propagate error
            raise

        # Keep track of whether the first telemetry from the sensor have been
        # read or not. If not then decoding errors will be ignored.
        self.first_telemetry_read = False

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
                self.log.info("Serial port opened.")
            except SerialException as e:
                self.log.exception("Serial port open failed.")
                raise e
        else:
            self.log.info("Port already open!")

    async def readline(self) -> str:
        """Read a line of telemetry from the device.

        Returns
        -------
        line : `str`
            Line read from the device. Includes terminator string if there is
            one. May be returned empty if nothing was received or partial if
            the readline was started during device reception.
        """
        terminator = self.sensor.terminator.encode(self.sensor.charset)

        # In order for the unit test to work, it is necessary to wrap this in
        # an ``asyncio.wait_for`` construction. Simply waiting for the
        # ``read_until_async`` method to return will make the unit test hang.
        bytes_read = await asyncio.wait_for(
            self.ser.read_until_async(expected=terminator), timeout=READ_TIMEOUT
        )

        # Always ignore the first line of telemetry from the sensor since it
        # may lead to decoding errors since the line may have only been
        # partially read.
        if not self.first_telemetry_read:
            self.first_telemetry_read = True
            st = self.sensor.terminator
        else:
            st = bytes_read.decode(encoding=self.sensor.charset)
        self.log.debug(f"Returning {st=}")
        return st

    async def basic_close(self) -> None:
        """Close the Sensor Device.

        Raises
        ------
        IOError if virtual communications port fails to close.
        """
        if self.ser.is_open:
            self.ser.close()
            self.log.exception("Serial port closed.")
        else:
            self.log.info("Serial port already closed.")
