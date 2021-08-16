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

__all__ = ["BaseMockTestCase"]

import math
import typing
import unittest

from lsst.ts.ess import common


class BaseMockTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.name = ""
        self.in_error_state = False
        self.num_channels = 0
        self.missed_channels = 0
        self.disconnected_channel: typing.Optional[int] = None
        self.reply = typing.Optional[typing.List[typing.Union[str, float]]]

    async def _callback(
        self, reply: typing.Dict[str, typing.List[typing.Union[str, float]]]
    ) -> None:
        self.reply = reply

    def check_hx85a_reply(self, reply: typing.List[typing.Union[str, float]]) -> None:
        device_name = reply[0]
        time = reply[1]
        response_code = reply[2]
        resp: typing.List[typing.SupportsFloat] = []
        for value in reply[3:]:
            assert isinstance(value, float)
            resp.append(value)

        self.assertEqual(self.name, device_name)
        self.assertGreater(time, 0)
        if self.in_error_state:
            self.assertEqual(common.ResponseCode.DEVICE_READ_ERROR, response_code)
        else:
            self.assertEqual(common.ResponseCode.OK, response_code)
        self.assertEqual(len(resp), 3)
        for i in range(0, 3):
            if i < self.missed_channels or self.in_error_state:
                self.assertTrue(math.isnan(resp[i]))
            else:
                if i == 0:
                    self.assertLessEqual(common.MockHumidityConfig.min, resp[i])
                    self.assertLessEqual(resp[i], common.MockHumidityConfig.max)
                elif i == 1:
                    self.assertLessEqual(common.MockTemperatureConfig.min, resp[i])
                    self.assertLessEqual(resp[i], common.MockTemperatureConfig.max)
                else:
                    self.assertLessEqual(common.MockDewPointConfig.min, resp[i])
                    self.assertLessEqual(resp[i], common.MockDewPointConfig.max)

    def check_hx85ba_reply(self, reply: typing.List[typing.Union[str, float]]) -> None:
        device_name = reply[0]
        time = reply[1]
        response_code = reply[2]
        resp: typing.List[typing.SupportsFloat] = []
        for value in reply[3:]:
            assert isinstance(value, float)
            resp.append(value)

        self.assertEqual(self.name, device_name)
        self.assertGreater(time, 0)
        if self.in_error_state:
            self.assertEqual(common.ResponseCode.DEVICE_READ_ERROR, response_code)
        else:
            self.assertEqual(common.ResponseCode.OK, response_code)
        self.assertEqual(len(resp), 3)
        for i in range(0, 3):
            if i < self.missed_channels or self.in_error_state:
                self.assertTrue(math.isnan(resp[i]))
            else:
                if i == 0:
                    self.assertLessEqual(common.MockHumidityConfig.min, resp[i])
                    self.assertLessEqual(resp[i], common.MockHumidityConfig.max)
                elif i == 1:
                    self.assertLessEqual(common.MockTemperatureConfig.min, resp[i])
                    self.assertLessEqual(resp[i], common.MockTemperatureConfig.max)
                else:
                    self.assertLessEqual(common.MockPressureConfig.min, resp[i])
                    self.assertLessEqual(resp[i], common.MockPressureConfig.max)

    def check_temperature_reply(
        self, reply: typing.List[typing.Union[str, float]]
    ) -> None:
        device_name = reply[0]
        time = reply[1]
        response_code = reply[2]
        resp: typing.List[typing.SupportsFloat] = []
        for value in reply[3:]:
            assert isinstance(value, float)
            resp.append(value)

        self.assertEqual(self.name, device_name)
        self.assertGreater(time, 0)
        if self.in_error_state:
            self.assertEqual(common.ResponseCode.DEVICE_READ_ERROR, response_code)
        else:
            self.assertEqual(common.ResponseCode.OK, response_code)
        self.assertEqual(len(resp), self.num_channels)
        for i in range(0, self.num_channels):
            if i < self.missed_channels or self.in_error_state:
                self.assertTrue(math.isnan(resp[i]))
            elif i == self.disconnected_channel:
                self.assertTrue(math.isnan(resp[i]))
            else:
                self.assertLessEqual(common.MockTemperatureConfig.min, resp[i])
                self.assertLessEqual(resp[i], common.MockTemperatureConfig.max)
