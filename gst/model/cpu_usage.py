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
from typing import List, Optional, Iterator


class CpuUsage:
    def __init__(self) -> None:
        self.cores: List[float] = []
        self.user: Optional[float] = None
        self.nice: Optional[float] = None
        self.system: Optional[float] = None
        self.io_wait: Optional[float] = None
        self.irq: Optional[float] = None
        self.soft_irq: Optional[float] = None
        self.steal: Optional[float] = None
        self.guest: Optional[float] = None
        self.guest_nice: Optional[float] = None

    def __iter__(self) -> Iterator:
        for attr, value in self.__dict__.items():
            yield attr, value
