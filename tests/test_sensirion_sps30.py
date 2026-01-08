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

import logging
from unittest.mock import patch

import sensirion_sps030
import serial

from lsst.ts.ess import common, controller


class SensirionSps30TestCase(controller.BaseRealSensorMockTestCase):
    async def test_sensirion_sps30(self) -> None:
        with (
            patch.object(sensirion_sps030.Sensirion, "read_measurement") as mock_read_measurement,
            patch.object(sensirion_sps030.Sensirion, "reset"),
            patch.object(sensirion_sps030.Sensirion, "_rx"),
            patch.object(sensirion_sps030.Sensirion, "_tx"),
            patch.object(serial.Serial, "open"),
        ):
            measurement = sensirion_sps030.SensirionReading(
                b"~\x00\x03\x00(?:\x86T@\xb8J\nA\x1d=RA>\x91\xa3\x00\x00\x00\x00>z\xe8\x00@\xa1\xba"
                b"\xdc@\xc0\x18\x1e@\xc4\xba\xea?\xd0\xa3\xd7\x17~"
            )
            mock_read_measurement.return_value = measurement

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

            # Validate the telemetry.
            await self.wait_for_read_event()
            assert self._reply is not None
            reply_to_check = self._reply[common.Key.TELEMETRY]
            telemetry = reply_to_check[common.Key.SENSOR_TELEMETRY]
            assert telemetry[2] == 0.5
            assert telemetry[3] == 1.0
            assert telemetry[4] == 2.5
            assert telemetry[5] == 4.0
            assert telemetry[6] == 10.0
            assert telemetry[7] == 0.0
            assert telemetry[8] == measurement.pm1
            assert telemetry[9] == measurement.pm25
            assert telemetry[10] == measurement.pm4
            assert telemetry[11] == measurement.pm10
            assert telemetry[12] == measurement.n05
            assert telemetry[13] == measurement.n1
            assert telemetry[14] == measurement.n25
            assert telemetry[15] == measurement.n4
            assert telemetry[16] == measurement.n10
            assert telemetry[17] == measurement.tps

            await self.device.close()
