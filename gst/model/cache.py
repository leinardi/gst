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
from typing import Optional, Any


class Cache:
    def __init__(self) -> None:
        self.id: Optional[int] = None
        self.level: Optional[int] = None
        self.number_of_sets: Optional[int] = None
        self.physical_package_id: Optional[int] = None
        self.size: Optional[int] = None
        self.type: Optional[str] = None
        self.ways_of_associativity: Optional[int] = None
        self.count: Optional[int] = 0

    def __eq__(self, other: Any) -> Any:
        return self.__dict__ == other.__dict__
