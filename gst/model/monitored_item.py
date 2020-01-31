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

from gst.util.sensors import FeatureType


class MonitoredItem:
    def __init__(self, item_id: str, name: str, value: Optional[float], value_type: FeatureType) -> None:
        self.item_id = item_id
        self.name = name
        self.value = value
        self.value_type = value_type
        self.value_min = value
        self.value_max = value

    def update_value(self, value: Optional[float]) -> None:
        self.value = value
        if value is not None:
            self.value_min = min(self.value_min, value) if self.value_min is not None else value
            self.value_max = max(self.value_max, value) if self.value_max is not None else value
