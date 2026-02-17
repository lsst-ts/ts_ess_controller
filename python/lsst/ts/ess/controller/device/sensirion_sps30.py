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

__all__ = ["SPS30", "SensirionSps30", "Sps30Command", "Sps30Reply", "unpack_measured_values"]

import asyncio
import datetime
import enum
import logging
import math
import struct
from typing import Callable

import serial

from lsst.ts import utils
from lsst.ts.ess import common

# Sleep time between reads [seconds].
READ_SLEEP_TIME = 0.9

# A minimal sleep time [seconds].
MINIMAL_SLEEP_TIME = 0.01

# The expected number of binary data items.
EXPECTED_DATA_LENGTH = 47

# The number of telemetry items.
TELEMETRY_LENGTH = 10

# Reconnect sleep time [seconds].
RECONNECT_SLEEP = 60.0

# Read timeout [sec].
READ_TIMEOUT = 10.0

# Maximum number of times to attempt a start or a stop.
MAX_NUM_START_STOP_ATTEMPS = 5

# Maximum number of times to attempt to read data.
MAX_NUM_READ_ATTEMPTS = 60

# Maximum number of bytes to read.
MAX_NUM_BYTES_TO_READ = 100

# Indices of bytes to check.
START_INDEX = 0
ADDR_INDEX = 1
ERROR_INDEX = 3
DATA_START_INDEX = 5
DATA_END_INDEX = 45

START_STOP = b"\x7e"


class Sps30Command(enum.Enum):
    """Commands to send to the sensor."""

    READ_MEASURED_VALUES = b"\x7e\x00\x03\x00\xfc\x7e"
    START_MEASUREMENT = b"\x7e\x00\x00\x02\x01\x03\xf9\x7e"
    STOP_MEASUREMENT = b"\x7e\x00\x01\x00\xfe\x7e"


class ErrorCode(enum.Enum):
    """Error codes that can be received from the sensor."""

    NO_ERROR = b"\x00"
    WRONG_DATA_LENGTH = b"\x01"
    UNKNOWN_COMMAND = b"\x02"
    NO_ACCESS_RIGHT_FOR_COMMAND = b"\x03"
    ILLEGAL_COMMAND_PARAMETER = b"\x04"
    INTERNAL_FUNCTION_ARGUMENT_OUT_OF_RANGE = b"\x28"
    COMMAND_NOT_ALLOWED_IN_CURRENT_STATE = b"\x43"


class Sps30Reply(enum.Enum):
    """Binary replies that can be received from the sensor."""

    CORRECT_START = b"\x7e\x00\x00\x00\x00\xff\x7e"
    CORRECT_STOP = b"\x7e\x00\x01\x00\x00\xfe\x7e"
    EMPTY = b"\x7e\x00\x03\x00\x00\xfc\x7e"
    INCORRECT_START = b"\x7e\x00\x00\x43\x00\xbc\x7e"
    INCORRECT_STOP = b"\x7e\x00\x01\x43\x00\xbb\x7e"


class StartMeasurementError(Exception):
    """Raised when the start measurement command fails."""

    pass


class StopMeasurementError(Exception):
    """Raised when the stop measurement command fails."""

    pass


class SPS30:
    """Serial interface to a Sensirion SPS30 sensor.

    This class implements a simple interface with the sensor. The sensor
    doesn't follow what is described in the data sheet
    (see https://ts-ess-common.lsst.io) very well and this interface aims to
    work around that by checking telemetry length and checksum and by
    swallowing exceptions raised when the sensor misbehaves.

    Attributes
    ----------
    serial : `serial.Serial`
        The serial object that is used to communicate with the sensor.
    log : `logging.Logger`
        The logger object that is used to log messages.

    Notes
    -----
    The rationale for design choices in the code is largely explained in the
    inline comments in the `SensirionSps30` class below.
    """

    def __init__(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.serial = serial.Serial(port="/dev/ttyUSB_upper_right", baudrate=115200, timeout=2)
        self.log.debug("Port opened successfully.")
        self._read_timer_task = utils.make_done_future()

    async def start_measurement(self) -> None:
        """Send the Start Measurement command to the sensor."""
        self.log.debug("Starting measurement.")
        hex_reply = b""
        error_value = -1
        num_attempts = 0
        while hex_reply != Sps30Reply.CORRECT_START.value and hex_reply != Sps30Reply.INCORRECT_START.value:
            num_attempts += 1
            try:
                await self._write_command_and_wait(Sps30Command.START_MEASUREMENT)
                hex_reply = await self._get_reply()
                if len(hex_reply) > 3:
                    error_value = hex_reply[3]
                    if error_value != 0:
                        self.log.warning(f"{error_value=} -> {ErrorCode(error_value)=}")
                if len(hex_reply) > len(Sps30Reply.CORRECT_START.value) or len(hex_reply) > len(
                    Sps30Reply.INCORRECT_START.value
                ):
                    break
            except (serial.serialutil.SerialException, ValueError) as e:
                raise StartMeasurementError("Failed to start measurement.") from e

            # Make sure that we don't end up in an endless loop.
            if num_attempts > MAX_NUM_START_STOP_ATTEMPS:
                raise StartMeasurementError(
                    f"Unable to start measurement after {MAX_NUM_START_STOP_ATTEMPS} attempts. Giving up."
                )

    async def read_measured_values(self) -> bytes:
        """Send the Read Measurements command to the sensor.

        Returns
        -------
        bytes
            The measured values as a binary string.
        """
        if self._read_timer_task.done():
            self._read_timer_task = asyncio.create_task(asyncio.sleep(READ_SLEEP_TIME))
        else:
            await self._read_timer_task
        self.log.debug("Reading measured values.")
        hex_reply = Sps30Reply.EMPTY.value
        num_attempts = 0
        while hex_reply == Sps30Reply.EMPTY.value:
            num_attempts += 1
            await self._write_command_and_wait(Sps30Command.READ_MEASURED_VALUES)
            hex_reply = await self._get_reply()
            if num_attempts > MAX_NUM_READ_ATTEMPTS:
                self.log.warning(
                    f"Unable to read measurement after {MAX_NUM_READ_ATTEMPTS} attempts. Giving up."
                )
                break
        return hex_reply

    async def stop_measurement(self) -> None:
        """Send the Stop Measurement command to the sensor."""
        self.log.debug("Stopping measurement.")
        hex_reply = b""
        error_value = -1
        num_attempts = 0
        while (
            hex_reply != Sps30Reply.CORRECT_STOP.value
            and hex_reply != Sps30Reply.INCORRECT_STOP.value
            and hex_reply != Sps30Reply.EMPTY.value
        ):
            num_attempts += 1
            try:
                await self._write_command_and_wait(Sps30Command.STOP_MEASUREMENT)
                hex_reply = await self._get_reply()
                if len(hex_reply) > 3:
                    error_value = hex_reply[3]
                    if error_value != 0:
                        self.log.warning(f"{error_value=} -> {ErrorCode(error_value)=}")
            except (serial.serialutil.SerialException, ValueError):
                # Do not raise an exception here. Retrying to stop the
                # measurement often works.
                self.log.warning(
                    f"Failed to stop measurement attempt {num_attempts} out of "
                    f"{MAX_NUM_START_STOP_ATTEMPS}. Ignoring."
                )

            # Make sure that we don't end up in an endless loop.
            if num_attempts > MAX_NUM_START_STOP_ATTEMPS:
                raise StopMeasurementError(
                    f"Unable to stop measurement after {MAX_NUM_START_STOP_ATTEMPS} attempts. Giving up."
                )

    async def _write_command_and_wait(self, command: Sps30Command) -> None:
        """Send a command to the sensor and wait so it can execute it..

        Parameters
        ----------
        command : `Sps30Command`
            The command to send.
        """
        self.serial.write(command.value)
        await asyncio.sleep(MINIMAL_SLEEP_TIME)

    async def _get_reply(self) -> bytes:
        """Run the blocking serial reading code in an executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._blocking_get_reply)

    def _blocking_get_reply(self) -> bytes:
        """Read the reply to a command from the sensor.

        Returns
        -------
        bytes
            The reply as a binary string.
        """
        hex_reply = b""
        c = 0
        bytes_read = 0
        end_reached = False
        while not end_reached:
            c = self.serial.read(1)
            if bytes_read == START_INDEX and c != START_STOP:
                raise ValueError(f"Did not receive START_STOP but {c=}.")
            elif bytes_read == ADDR_INDEX and ord(c) != 0:
                raise ValueError(f"Did not receive ADDR==0 but {c=}")
            elif bytes_read == ERROR_INDEX and ord(c) != 0:
                self.log.warning(f"Got state error {ErrorCode(c)=}.")
            elif bytes_read >= DATA_START_INDEX and c == START_STOP:
                end_reached = True
            elif bytes_read > MAX_NUM_BYTES_TO_READ:
                self.log.warning(f"Number of bytes read exceeded {MAX_NUM_BYTES_TO_READ}. Giving up.")
                end_reached = True

            hex_reply += c
            bytes_read += 1
        return hex_reply

    async def stop_and_start(self) -> None:
        """Stop and start the measurements.

        This is a convenience method that ensures that stopping and starting
        is performed until both are successful. This is necessary to ensure
        that the sensor outputs sensible measurements again.
        """
        success = False

        # This is not an endless loop. After MAX_NUM_START_STOP_ATTEMPS an
        # exception is thrown ending the loop.
        while not success:
            await self.stop_measurement()
            await asyncio.sleep(MINIMAL_SLEEP_TIME)
            await self.start_measurement()
            success = True


async def compute_checksum(binary_data: bytes) -> int:
    """Compute the checksum of a byte array.

    Parameters
    ----------
    binary_data : `bytes`
        The data to compute the checksum of.

    Returns
    -------
    int
        The computed checksum.

    Notes
    -----
    The data sheet (see https://ts-ess-common.lsst.io) explains how to compute
    the checksum.
    """
    int_data = [x for x in binary_data[1:-2]]
    sum_bytes = bytes([sum(int_data) % 256])
    # Get the least significant bit.
    lsb = ord(sum_bytes) >> 0
    # Inverting it gets the checksum.
    checksum = 255 - lsb
    return checksum


async def unpack_measured_values(binary_data: bytes) -> list[float]:
    """Unpack the measured values from the sensor.

    Parameters
    ----------
    binary_data : `bytes`
        The binary data to unpack.

    Returns
    -------
    `list` of `float`
        The unpacked values.

    Notes
    -----
    The vbinary data passed on must only contain the actual telemetry, and
    should not include the header and footer of the binary data received from
    the sensor. The data sheet (see https://ts-ess-common.lsst.io) explains
    the binary data format.
    """
    if len(binary_data) != 40:
        return [math.nan] * 10
    return [
        round(struct.unpack(">f", binary_data[0:4])[0], 1),
        round(struct.unpack(">f", binary_data[4:8])[0], 1),
        round(struct.unpack(">f", binary_data[8:12])[0], 1),
        round(struct.unpack(">f", binary_data[12:16])[0], 1),
        round(struct.unpack(">f", binary_data[16:20])[0], 1),
        round(struct.unpack(">f", binary_data[20:24])[0], 1),
        round(struct.unpack(">f", binary_data[24:28])[0], 1),
        round(struct.unpack(">f", binary_data[28:32])[0], 1),
        round(struct.unpack(">f", binary_data[32:36])[0], 1),
        round(struct.unpack(">f", binary_data[36:40])[0], 1),
    ]


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
        self.sps30: SPS30 | None = None

        # Keep track of the previous time a readline was performed.
        self.previous_readline_time: datetime.datetime | None = None

    async def basic_open(self) -> None:
        """Open a connection to the device.

        Also send a STOP and then a START to ensure that the sensor is ready
        for requests of measured values.
        """
        if self.sps30 is None:
            self.sps30 = SPS30()

        self.open_event.set()
        # Always first send a stop in case this wasn't sent before, or if that
        # resulted in an exception. This may result in a
        # COMMAND_NOT_ALLOWED_IN_CURRENT_STATE error but that can be ignored.
        await self.sps30.stop_and_start()

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

        assert self.sps30 is not None

        try:
            hex_reply = await self.sps30.read_measured_values()
            current_tai = utils.current_tai()
            checksum = await compute_checksum(hex_reply)
            hex_checksum = hex_reply[-2]

            # Sometimes the sensor emits telemetry that is too short or too
            # long. No idea why but the telemetry itself claims that it is
            # of the correct length when it really is not. In such a case the
            # telemetry needs to be discarded.
            if len(hex_reply) != EXPECTED_DATA_LENGTH:
                self.log.debug(f"Invalid data length: {len(hex_reply)} != {EXPECTED_DATA_LENGTH}.")

            # When the telemetry length is incorrect, so is the checksum, and
            # it looks like that is the only case. But better safe than sorry
            # so if the computed checksum doesn't match the telemetry
            # checksum, the telemetry needs to be discarded as well.
            elif checksum != hex_checksum:
                self.log.debug(f"Invalid checksum: {checksum} != {hex_checksum}.")

            # If the telemetry passes the previous checks, it can be
            # processed. The binary telemetry needs to be unpacked, and then
            # it can be sent to the CSC for further processing.
            else:
                telemetry = await unpack_measured_values(hex_reply[DATA_START_INDEX:DATA_END_INDEX])
                self.log.debug(f"{telemetry=}.")
                line = f"{current_tai},{0.0}," + ",".join([f"{x:1.1f}" for x in telemetry])
        except (serial.serialutil.SerialException, ValueError):
            # Occasionally the sensor doesn't return telemetry and an
            # exception is raised. In such a case a stop and then a start
            # needs to be sent to make the telemetry flow again.
            await self.sps30.stop_and_start()

        now = datetime.datetime.now(datetime.UTC)
        if self.previous_readline_time is not None:
            interval = (now - self.previous_readline_time).total_seconds()
            if interval > self.read_timeout:
                self.log.warning(f"Previous {self.name} readline was {interval} seconds ago.")
        self.previous_readline_time = now

        self.log.debug(f"Returning {self.name} {line=}.")
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
        """Close the Sensor Device."""
        if self.sps30 is not None:
            # This may result in an exception which is swallowed by the method.
            # The result is that the measurements are not stopped, which is not
            # a problem because the telemetry is not read anymore and the
            # sensor doesn't suffer from it. But it is one of the reasons why
            # this same method is called when a connection to the sensor is
            # made.
            try:
                await self.sps30.stop_measurement()
            finally:
                self.sps30 = None
