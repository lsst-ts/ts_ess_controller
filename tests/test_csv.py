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

import os
import tempfile
import csv

from lsst.ts.ess.controller.device.csv import CSVDevice
from lsst.ts.ess.common.sensor.sps30 import Sps30Sensor
from lsst.ts.ess.controller.base_real_sensor_mock_test_case import BaseRealSensorMockTestCase


class CsvDeviceTestCase(BaseRealSensorMockTestCase):
    async def test_csv_device_reads_expected_data(self):
        # Setup temporary CSV file with test data
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, newline="") as temp_csv:
            writer = csv.DictWriter(temp_csv, fieldnames=["pm1.0", "pm2.5", "pm4.0", "pm10"])
            writer.writeheader()
            writer.writerow({"pm1.0": "0.1", "pm2.5": "0.2", "pm4.0": "0.3", "pm10": "0.4"})
            writer.writerow({"pm1.0": "0.5", "pm2.5": "0.6", "pm4.0": "0.7", "pm10": "0.8"})
            temp_csv_path = temp_csv.name

        # Use real SPS30 sensor (won’t communicate with hardware in CSV mode)
        self.sensor = Sps30Sensor(name="test_sensor", field_map={})
        self.device = CSVDevice(
            name="CSVDevice",
            csv_path=temp_csv_path,
            sensor=self.sensor,
            callback_func=self._callback,
            log=self.log,
        )

        # Read first line
        await self.device.open()
        await self.wait_for_read_event()
        assert self._reply is not None
        telemetry = self._reply["telemetry"]
        assert telemetry["pm1.0"] == 0.1
        assert telemetry["pm2.5"] == 0.2

        # Read second line
        await self.wait_for_read_event()
        telemetry = self._reply["telemetry"]
        assert telemetry["pm10"] == 0.8

        await self.device.close()
        os.remove(temp_csv_path)
