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

import asyncio
import enum
import logging
import math
import struct
from unittest.mock import patch

import serial

from lsst.ts.ess import common, controller


class Measurement(enum.Enum):
    """Measurement binary data taken from the real device.

    The correct data should provide numeric telemetry, the incorrect data
    only nans.
    """

    CORRECT = (
        b"~\x00\x03\x00(?:\x86T@\xb8J\nA\x1d=RA>\x91\xa3\x00\x00\x00\x00>z\xe8\x00@\xa1\xba"
        b"\xdc@\xc0\x18\x1e@\xc4\xba\xea?\xd0\xa3\xd7\x17~"
    )
    TOO_LONG = (
        b"~\x00\x03\x00(?\x8b\xe4\xbfA\n7\x88Ak\xdb\xfbA\x8e\xed:\x00\x00\x00\x00>\xbc.\x00@"
        b"\xf2\x98JA\x10\x12\x16A}3\x8c0?\xd0\xa3\xd7\x97~"
    )


class SensirionSps30TestCase(controller.BaseRealSensorMockTestCase):
    async def test_sensirion_sps30(self) -> None:
        self.device_stopped = True
        self.stop_raises_exception = False
        self.start_raises_exception = False

        with (
            patch.object(serial.Serial, "open"),
            patch.object(serial.Serial, "read", self.read),
            patch.object(serial.Serial, "write", self.write),
        ):
            log = logging.getLogger(type(self).__name__)
            sensor = common.sensor.Sps30Sensor(log=log)
            self.device = controller.device.SensirionSps30(
                name="Test",
                device_id="/dev/ttyUSB0",
                sensor=sensor,
                baud_rate=0,
                callback_func=self._callback,
                log=log,
            )

            for self.measurement in Measurement:
                await self.device.open()

                # Validate the telemetry.
                await self.wait_for_read_event()
                assert self._reply is not None
                reply_to_check = self._reply[common.Key.TELEMETRY]
                telemetry = reply_to_check[common.Key.SENSOR_TELEMETRY]

                match self.measurement:
                    case Measurement.CORRECT:
                        expected_values = await controller.device.unpack_measured_values(
                            Measurement.CORRECT.value[5:45]
                        )
                        assert telemetry[1] == 0.5
                        assert telemetry[2] == 1.0
                        assert telemetry[3] == 2.5
                        assert telemetry[4] == 4.0
                        assert telemetry[5] == 10.0
                        assert telemetry[6] == 0.0
                        for i in range(7, 17):
                            assert telemetry[i] == expected_values[i - 7]
                    case Measurement.TOO_LONG:
                        for i in range(1, 17):
                            assert math.isnan(telemetry[i])

                await self.device.close()

    async def test_start_or_stop_raises_exception(self) -> None:
        self.device_stopped = True
        for self.stop_raises_exception, self.start_raises_exception in [(True, False), (False, True)]:
            with (
                patch.object(serial.Serial, "open"),
                patch.object(serial.Serial, "read", self.read),
                patch.object(serial.Serial, "write", self.write),
            ):
                log = logging.getLogger(type(self).__name__)
                sensor = common.sensor.Sps30Sensor(log=log)
                self.device = controller.device.SensirionSps30(
                    name="Test",
                    device_id="/dev/ttyUSB0",
                    sensor=sensor,
                    baud_rate=0,
                    callback_func=self._callback,
                    log=log,
                )

                await self.device.open()
                await asyncio.sleep(0.1)
                # No need to assert anything. This should not hang.
                await self.device.close()

    def read(self, size: int = 1) -> bytes:
        bytes_to_return = self.reply_to_send[self.reply_char_count]
        self.reply_char_count += 1
        return bytes_to_return

    def write(self, data: bytes) -> None:
        self.sps30_command = controller.device.Sps30Command(data)
        self.reply_char_count = 0
        match self.sps30_command:
            case controller.device.Sps30Command.STOP_MEASUREMENT:
                if self.stop_raises_exception:
                    raise serial.serialutil.SerialException("Test.")
                if not self.device_stopped:
                    reply_to_send = controller.device.Sps30Reply.CORRECT_STOP.value
                else:
                    reply_to_send = controller.device.Sps30Reply.INCORRECT_STOP.value
                self.device_stopped = True
            case controller.device.Sps30Command.START_MEASUREMENT:
                if self.start_raises_exception:
                    raise serial.serialutil.SerialException("Test.")
                if self.device_stopped:
                    reply_to_send = controller.device.Sps30Reply.CORRECT_START.value
                else:
                    reply_to_send = controller.device.Sps30Reply.INCORRECT_START.value
                self.device_stopped = False
            case controller.device.Sps30Command.READ_MEASURED_VALUES:
                reply_to_send = self.measurement.value
            case _:
                raise ValueError("Unknown command.")

        self.reply_to_send = struct.unpack(str(len(reply_to_send)) + "c", reply_to_send)
