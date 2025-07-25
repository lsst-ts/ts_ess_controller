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

from lsst.ts.ess import common, controller


class VcpFtdiTestCase(controller.BaseRealSensorMockTestCase):
    async def verify_vcp_ftdi(self) -> None:
        self.return_as_plain_text = True
        name = "MockedVcpFtdi"
        self.num_channels = 2
        self.sensor.num_channels = self.num_channels
        self.device = controller.device.VcpFtdi(
            name=name,
            device_id="ABCDEF",
            sensor=self.sensor,
            baud_rate=19200,
            callback_func=self._callback,
            log=self.log,
            use_mock_device=True,
            read_generates_error=self.read_generates_error,
            generate_timeout=self.generate_timeout,
        )
        self.device.read_timeout = 1.0
        self.device.reconnect_sleep = 1.0

        await self.device.open()

        await self.wait_for_read_event()
        assert self._reply is not None
        if self.generate_timeout or self.read_generates_error:
            assert self._reply == {}
        else:
            reply_to_check = self._reply[common.Key.TELEMETRY]
            self.mtt.check_temperature_reply(
                reply=reply_to_check,
                name=name,
                num_channels=self.num_channels,
                in_error_state=self.read_generates_error,
            )

        await self.wait_for_read_event()
        assert self._reply is not None
        if self.generate_timeout or self.read_generates_error:
            assert self._reply == {}
        else:
            reply_to_check = self._reply[common.Key.TELEMETRY]
            self.mtt.check_temperature_reply(
                reply=reply_to_check,
                name=name,
                num_channels=self.num_channels,
                in_error_state=self.read_generates_error,
            )

        await self.device.close()

    async def test_vcp_ftdi_with_normal_terminator(self) -> None:
        self.add_null_character_in_terminator = False
        await self.verify_vcp_ftdi()

    async def test_vcp_ftdi_with_enhanced_terminator(self) -> None:
        self.add_null_character_in_terminator = True
        await self.verify_vcp_ftdi()

    async def test_vcp_ftdi_with_read_error(self) -> None:
        self.read_generates_error = True
        await self.verify_vcp_ftdi()

    async def test_vcp_ftdi_with_timeout(self) -> None:
        self.generate_timeout = True
        await self.verify_vcp_ftdi()
