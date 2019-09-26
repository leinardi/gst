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
from typing import Dict, Optional

from gst.model.monitored_item import MonitoredItem
from gst.util.sensors import FeatureType


class HardwareMonitor:
    def __init__(self) -> None:
        self.hw_monitored_items: Dict[str, Dict[FeatureType, Dict[str, MonitoredItem]]] = {}

    def get_hw_monitored_item(self,
                              chip_id: str,
                              feature_type: FeatureType,
                              item_id: str) -> Optional[MonitoredItem]:
        chip = self.hw_monitored_items.get(chip_id)
        if chip is None:
            return None
        feature_type_dict = chip.get(feature_type)
        if feature_type_dict is None:
            return None
        return feature_type_dict.get(item_id)

    def set_hw_monitored_item(self, chip_id: str, item: MonitoredItem) -> None:
        item_id = item.item_id
        feature_type = item.value_type
        old_item = self.get_hw_monitored_item(chip_id, feature_type, item_id)
        if old_item is None:
            chip = self.hw_monitored_items.get(chip_id)
            if chip is None:
                chip = {}
                self.hw_monitored_items[chip_id] = chip
            feature_type_dict = chip.get(feature_type)
            if feature_type_dict is None:
                feature_type_dict = {}
                chip[feature_type] = feature_type_dict
            old_item = feature_type_dict.get(item_id)
            if old_item is None:
                feature_type_dict[item_id] = item
                return
        if old_item.item_id != item.item_id:
            raise ValueError(f"Trying to update a Core with a different id: "
                             f"{old_item.item_id} != {item.item_id}")
        old_item.update_value(item.value)
