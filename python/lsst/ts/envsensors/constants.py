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

__all__ = [
    "CMD_CONFIGURE",
    "CMD_START",
    "CMD_STOP",
    "KEY_CHANNELS",
    "KEY_DEVICES",
    "KEY_FTDI_ID",
    "KEY_NAME",
    "KEY_RESPONSE",
    "KEY_SERIAL_PORT",
    "KEY_TELEMETRY",
    "KEY_TYPE",
    "VAL_FTDI",
    "VAL_SERIAL",
]

# Command and configuration key and value constants.
CMD_CONFIGURE = "configure"
CMD_START = "start"
CMD_STOP = "stop"
KEY_CHANNELS = "channels"
KEY_DEVICES = "devices"
KEY_FTDI_ID = "ftdi_id"
KEY_NAME = "name"
KEY_RESPONSE = "response"
KEY_SERIAL_PORT = "serial_port"
KEY_TELEMETRY = "telemetry"
KEY_TYPE = "type"
VAL_FTDI = "FTDI"
VAL_SERIAL = "Serial"
