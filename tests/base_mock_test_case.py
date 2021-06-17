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

__all__ = ["BaseMockTestCase"]

import math
import unittest

from lsst.ts.envsensors import Temperature, DISCONNECTED_VALUE, ResponseCode


class BaseMockTestCase(unittest.IsolatedAsyncioTestCase):
    def check_reply(self, reply):
        device_name = reply[0]
        time = reply[1]
        response_code = reply[2]
        resp = reply[3:]

        self.assertEqual(self.name, device_name)
        self.assertGreater(time, 0)
        self.assertEqual(ResponseCode.OK, response_code)
        self.assertEqual(len(resp), self.num_channels)
        for i in range(0, self.num_channels):
            if i < self.missed_channels:
                self.assertTrue(math.isnan(resp[i]))
            elif i == self.disconnected_channel:
                self.assertTrue(math.isnan(resp[i]))
            else:
                self.assertLessEqual(Temperature.MIN, resp[i])
                self.assertLessEqual(resp[i], Temperature.MAX)