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

__all__ = ["Command", "DeviceType", "Key"]

import enum


class Command(str, enum.Enum):
    """Commands accepted by the Socket Server and Command Handler."""

    CONFIGURE = "configure"
    DISCONNECT = "disconnect"
    EXIT = "exit"
    START = "start"
    STOP = "stop"


class DeviceType(str, enum.Enum):
    """Supported device types."""

    FTDI = "FTDI"
    SERIAL = "Serial"


class Key(str, enum.Enum):
    """Keys that may be present in the device configuration or as command
    parameters."""

    CHANNELS = "channels"
    CONFIGURATION = "configuration"
    DEVICES = "devices"
    FTDI_ID = "ftdi_id"
    NAME = "name"
    RESPONSE = "response"
    SERIAL_PORT = "serial_port"
    TELEMETRY = "telemetry"
    TYPE = "type"
