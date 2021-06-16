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

__all__ = ["DeviceConfig"]

from typing import Dict, Union

from .constants import Key


class DeviceConfig:
    """Container for device configurations.

    Parameters
    ----------
    name: `str`
        The name of the device.
    channels: `int`
        The number of channels the output data.
    dev_type: `str`
        The type of device.
    dev_id: `str`
        The ID of the device.
    sens_type: `str`
        The type of sensor.

    """

    def __init__(
        self, name: str, channels: int, dev_type: str, dev_id: str, sens_type: str
    ) -> None:
        self.name = name
        self.channels = channels
        self.dev_type = dev_type
        self.dev_id = dev_id
        self.sens_type = sens_type

    def as_dict(self) -> Dict[str, Union[str, int]]:
        """Return a dict with the instance attributes and their values as
        key-value pairs.

        Returns
        -------
        dict: `dict`
            A dictionary of key-value pairs representing the instance
            attributes and their values.
        """
        return {
            Key.NAME: self.name,
            Key.CHANNELS: self.channels,
            Key.DEVICE_TYPE: self.dev_type,
            Key.FTDI_ID: self.dev_id,
            Key.SENSOR_TYPE: self.sens_type,
        }
