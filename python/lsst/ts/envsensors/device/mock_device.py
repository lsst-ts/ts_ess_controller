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

__all__ = ["MockDevice"]

import logging
from typing import Callable

from ..sensor import BaseSensor
from .base_device import BaseDevice


class MockDevice(BaseDevice):
    """Mock Sensor Device.

    Parameters:
    -----------
    device_id: `str`
        The hardware device ID to connect to.
    sensor: `BaseSensor`
        The sensor that produces the telemetry.
    callback_func : `Callable`
        Callback function to receive the telemetry.
    """

    def __init__(
        self,
        device_id: str,
        sensor: BaseSensor,
        callback_func: Callable,
        log: logging.Logger,
    ) -> None:
        super().__init__(
            device_id=device_id, sensor=sensor, callback_func=callback_func, log=log
        )

    def init(self) -> None:
        """Initialize the Sensor Device."""
        pass

    async def open(self) -> None:
        """Open the Sensor Device."""
        pass

    async def close(self) -> None:
        """Close the Sensor Device."""
        pass
