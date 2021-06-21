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

__all__ = ["RpiSerialHat"]

import logging
from typing import Callable

from .base_device import BaseDevice
from ..sensor import BaseSensor


class RpiSerialHat(BaseDevice):
    """USB Virtual Communications Port (VCP) for FTDI device.

    Parameters:
    -----------
    device_id: `str`
        The hardware device ID to connect to. This can be a physical ID (e.g.
        /dev/ttyUSB0), a serial port (e.g. serial_ch_1) or any other ID used by
        the specific device.
    sensor: `BaseSensor`
        The sensor that produces the telemetry.
    callback_func : `Callable`
        Callback function to receive instrument output.

    Notes
    -----
    This is a skeleton class that will be implemented further as soon as I get
    my hands on a raspberry pi with a serial hat.
    """

    def __init__(
        self,
        name: str,
        device_id: str,
        sensor: BaseSensor,
        callback_func: Callable,
        log: logging.Logger,
    ) -> None:
        super().__init__(
            name=name,
            device_id=device_id,
            sensor=sensor,
            callback_func=callback_func,
            log=log,
        )

    def init(self) -> None:
        """Initialize the Sensor Device."""
        pass

    async def basic_open(self) -> None:
        """Open the Sensor Device.

        Raises
        ------
        IOError if virtual communications port fails to open.
        """
        pass

    async def readline(self) -> str:
        """Read a line of telemetry from the Device.

        Returns
        -------
        output: `str`
            A line of telemetry.

        Raises
        ------
        NotImplementedError
            This method will be implemented later.
        """
        raise NotImplementedError("This function has not yet been implemented.")

    async def basic_close(self) -> None:
        """Close the Sensor Device.

        Raises
        ------
        IOError if virtual communications port fails to close.
        """
        pass
