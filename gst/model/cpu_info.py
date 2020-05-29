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
from typing import List, Dict, Optional

from gst.model import SelectedProcessor
from gst.model.monitored_item import MonitoredItem
from gst.model.processor import Processor, ProcessorDict


class CpuInfo:
    def __init__(self) -> None:
        self.physical_package_id_list: List[ProcessorDict] = []
        self.clock_monitored_items: Dict[int, Dict[int, MonitoredItem]] = {}

    def get_processor(self, selected_processor: SelectedProcessor) -> Processor:
        physical_package_id = selected_processor[0]
        processor_id = selected_processor[1]
        if physical_package_id is not None and processor_id is not None:
            if len(self.physical_package_id_list) < physical_package_id + 1:
                self.physical_package_id_list.append({})
            if processor_id not in self.physical_package_id_list[physical_package_id]:
                self.physical_package_id_list[physical_package_id][processor_id] = Processor()
            return self.physical_package_id_list[physical_package_id][processor_id]
        raise ValueError("selected_processor must not have None values")

    def get_clock_monitored_item(self, physical_package_id: int, core_id: int) -> Optional[MonitoredItem]:
        ppi = self.clock_monitored_items.get(physical_package_id)
        return None if ppi is None else ppi.get(core_id)

    def set_clock_monitored_item(self, physical_package_id: int, item: MonitoredItem) -> None:
        core_id = int(item.item_id)
        old_item = self.get_clock_monitored_item(physical_package_id, core_id)
        if old_item is None:
            physical_package = self.clock_monitored_items.get(physical_package_id)
            if physical_package is None:
                physical_package = {}
                self.clock_monitored_items[physical_package_id] = physical_package
            old_item = physical_package.get(core_id)
            if old_item is None:
                physical_package[core_id] = item
                return
        if old_item.item_id != item.item_id:
            raise ValueError(f"Trying to update a Core with a different id: "
                             f"{old_item.item_id} != {item.item_id}")
        old_item.update_value(item.value)
