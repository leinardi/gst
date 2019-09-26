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
from typing import Optional, List, Dict

from gst.model import SelectedProcessor
from gst.model.cache import Cache


class Processor:
    def __init__(self) -> None:
        self.bogomips: Optional[float] = None
        self.bugs: Optional[List[str]] = None
        self.bus_speed: Optional[int] = None
        self.cache_l1_data: Optional[Cache] = None
        self.cache_l1_inst: Optional[Cache] = None
        self.cache_l2: Optional[Cache] = None
        self.cache_l3: Optional[Cache] = None
        self.codename: Optional[str] = None
        self.core_id: Optional[int] = None
        self.core_speed: Optional[float] = None
        self.cores: Optional[int] = None
        self.default_bus_speed: Optional[int] = None
        self.default_multiplier: Optional[float] = None
        self.family: Optional[int] = None
        self.flags: Optional[List[str]] = None
        self.lithography: Optional[float] = None
        self.max_tdp: Optional[int] = None
        self.microcode: Optional[int] = None
        self.model: Optional[int] = None
        self.multiplier: Optional[float] = None
        self.name: Optional[str] = None
        self.physical_package_id: Optional[int] = None
        self.processor_id: Optional[int] = None
        self.rated_fsb: Optional[int] = None
        self.package: Optional[str] = None
        self.specification: Optional[str] = None
        self.stepping: Optional[int] = None
        self.threads: Optional[int] = None
        self.v_core: Optional[int] = None
        self.vendor_id: Optional[str] = None

    def get_selected_processor(self) -> SelectedProcessor:
        return [self.physical_package_id, self.processor_id]


ProcessorDict = Dict[int, Processor]
