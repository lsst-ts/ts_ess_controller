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

__all__ = ["MockSerial"]

import time

# The reply that is repeated over and over.
MOCK_REPLY = "C01=0022.1443,C02=0023.0320\r\n"

# The amount of timne to sleep [sec] to mimick a timeout.
TIMEOUT_SLEEP = 30.0


class MockSerial:
    """Mock serial device class for testing purposes.

    Returns the same temperature string over and over again.

    Parameters
    ----------
    read_generates_error : `bool`
        Does reading the divice generate a RuntimeError or not.
    encode_reply : `bool`
        Encode the reply or not.
    generate_timeout : `bool`
        Does reading the divice take very long or not.
    """

    def __init__(
        self, read_generates_error: bool, encode_reply: bool, generate_timeout: bool
    ) -> None:
        self.is_open = False
        self.baudrate = 0
        self.char_count = 0
        self.read_generates_error = read_generates_error
        self.encode_reply = encode_reply
        self.generate_timeout = generate_timeout

    @property
    def closed(self) -> bool:
        return not self.is_open

    def flush(self) -> None:
        # Deliberately left empty.
        pass

    def open(self) -> None:
        self.is_open = True

    def read(self, size: int = 1) -> bytes | str:
        if self.read_generates_error:
            raise RuntimeError("Raising error on purpose.")
        if self.generate_timeout:
            time.sleep(TIMEOUT_SLEEP)
        if self.char_count >= len(MOCK_REPLY):
            self.char_count = 0
        b: bytes | str = f"{MOCK_REPLY[self.char_count]}"
        if self.encode_reply:
            assert isinstance(b, str)
            b = b.encode()
        self.char_count += 1
        return b

    def close(self) -> None:
        self.is_open = False
