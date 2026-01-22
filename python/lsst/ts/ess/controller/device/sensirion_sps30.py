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

__all__ = ["SensirionSps30"]

import asyncio
import datetime
import logging
from typing import Callable

import serial
from sensirion_sps030 import Sensirion, SensirionException, SensirionReading

from lsst.ts import utils
from lsst.ts.ess import common

# Reconnect sleep time [seconds].
RECONNECT_SLEEP = 60.0

# Read timeout [sec].
READ_TIMEOUT = 10.0

# Sleep time [sec] between stopping and restarting measurements.
STOP_START_SLEEP = 0.02


class SensirionSps30(common.device.BaseDevice):
    """Sensirion SPS30 telemetry reader.

    Parameters
    ----------
    name : `str`
        The name of the device.
    device_id : `str`
        The hardware device ID to connect to. This needs to be a physical ID
        (e.g. /dev/ttyUSB0).
    callback_func : `Callable`
        Callback function to receive the telemetry.
    log : `logging.Logger`
        The logger to create a child logger for.
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
    ) -> None:
        super().__init__(
            name=name,
            device_id=device_id,
            sensor=sensor,
            baud_rate=0,
            callback_func=callback_func,
            log=log,
        )
        self.sensirion: Sensirion | None = None

        # Keep track of the previous time a readline was performed.
        self.previous_readline_time: datetime.datetime | None = None

    async def basic_open(self) -> None:
        """Open and configure serial port.
        Open the serial communications port and set BAUD.

        Raises
        ------
        IOError if serial communications port fails to open.
        """
        if self.sensirion is None:
            self.sensirion = Sensirion(
                port=self.device_id, log_level=logging.ERROR, auto_start=False, retries=1
            )
        self.sensirion.start_measurement()

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
                line = await loop.run_in_executor(None, self._blocking_readline)
        except (serial.SerialException, SensirionException):
            assert self.sensirion is not None
            self.log.debug("Stopping measurements.")
            self.sensirion.stop_measurement()
            await asyncio.sleep(STOP_START_SLEEP)
            self.log.debug("Starting measurements.")
            self.sensirion.start_measurement()
        except TimeoutError:
            self.log.exception(f"Timeout reading {self.name}. So far {line=!r}.")
            raise

        now = datetime.datetime.now(datetime.UTC)
        if self.previous_readline_time is not None:
            interval = (now - self.previous_readline_time).total_seconds()
            if interval > self.read_timeout:
                self.log.warning(f"Previous {self.name} readline was {interval} seconds ago.")
        self.previous_readline_time = now

        self.log.debug(f"Returning {self.name} {line=}.")
        return line

    def _blocking_readline(self) -> str:
        assert self.sensirion is not None
        measurement: SensirionReading = self.sensirion.read_measurement()
        timestamp_utc = datetime.datetime.strptime(measurement.timestamp, "%Y-%m-%d %H:%M:%S").astimezone(
            datetime.timezone.utc
        )
        current_tai = utils.tai_from_utc_unix(timestamp_utc.timestamp())
        line = (
            f"{current_tai},{0.0},{measurement.pm1},{measurement.pm25},{measurement.pm4},{measurement.pm10},"
            f"{measurement.n05},{measurement.n1},{measurement.n25},{measurement.n4},{measurement.n10},"
            f"{measurement.tps}"
        )
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
            await self.close()
            await asyncio.sleep(self.reconnect_sleep)
            raise

    async def basic_close(self) -> None:
        """Close the Sensor Device."""
        assert self.sensirion is not None
        self.sensirion.stop_measurement()
        self.sensirion = None
