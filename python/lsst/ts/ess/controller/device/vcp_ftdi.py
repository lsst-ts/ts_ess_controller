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
import concurrent
import logging
from typing import Callable

from lsst.ts.ess import common
from pylibftdi import Device


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
        self.vcp: Device = Device(
            self.device_id,
            mode="t",
            encoding="ASCII",
            lazy_open=True,
            auto_detach=False,
        )

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
            self.log.debug("FTDI device open.")
            self.vcp.flush()
        else:
            self.log.error("Failed to open the FTDI device.")
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            while not line.endswith(self.sensor.terminator):
                line += await loop.run_in_executor(pool, self.vcp.read, 1)
        return line

    async def basic_close(self) -> None:
        """Close the Sensor Device.

        Raises
        ------
        IOError if virtual communications port fails to close.
        """
        self.vcp.close()
        if self.vcp.closed:
            self.log.debug("FTDI device closed.")
        else:
            self.log.debug("FTDI device failed to close.")
            raise IOError(f"VcpFtdi:{self.name}: Failed to close the FTDI device.")
