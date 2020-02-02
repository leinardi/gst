# This file is part of gst.
#
# Copyright (c) 2020 Roberto Leinardi
#
# gst is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gst is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gst.  If not, see <http://www.gnu.org/licenses/>.
from typing import Optional

LOCATOR_DEFAULT_TEXT = ""
BANK_LOCATOR_DEFAULT_TEXT = "Click \"Read all\""


class MemoryBankInfo:
    def __init__(self) -> None:
        self.locator: Optional[str] = LOCATOR_DEFAULT_TEXT
        self.bank_locator: Optional[str] = BANK_LOCATOR_DEFAULT_TEXT
        self.type: Optional[str] = None
        self.type_detail: Optional[str] = None
        self.size: Optional[str] = None
        self.speed: Optional[str] = None
        self.rank: Optional[str] = None
        self.manufacturer: Optional[str] = None
        self.part_number: Optional[str] = None
        self.serial_number: Optional[str] = None
