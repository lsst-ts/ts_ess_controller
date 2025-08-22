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

import csv
from typing import Any
# from lsst.ts.ess.common.device.base_device import BaseDevice

class CSVDevice(BaseDevice):
    def __init__(
        self,
        name: str,
        csv_path: str,
        sensor: Any,
        callback_func: Any,
        log: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name,
            device_id="CSV",
            sensor=sensor,
            callback_func=callback_func,
            log=log,
        )
        self.csv_path = csv_path

    async def start(self) -> None:
        self.log.info(f"Reading CSV from {self.csv_path}")
        try:
            with open(self.csv_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data = {k: float(v) for k, v in row.items()}
                    self.callback_func(data)
        except Exception as e:
            self.log.error(f"Error reading CSV: {e}")

    async def stop(self) -> None:
        pass

