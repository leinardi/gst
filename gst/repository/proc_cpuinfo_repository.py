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
import logging
import os
import re
import threading
from typing import List, Optional, Dict

from injector import singleton, inject

from gst.model.monitored_item import MonitoredItem
from gst.model.processor import Processor
from gst.model.system_info import SystemInfo
from gst.util.concurrency import synchronized_with_attr
from gst.util.sensors import FeatureType

_LOG = logging.getLogger(__name__)
PATH_PROC_CPUINFO = '/proc/cpuinfo'
CLEAN_CPU_STRING_REGEX = r"chipset|company|components|computing|computer|corporation|communications|electronics|" \
                         r"electrical|electric|gmbh|group|incorporation|industrial|international|\bnee\b|revision" \
                         r"|semiconductor|software|technologies|technology|ltd\.|<ltd>|\bltd\b|inc\.|<inc>|\binc\b" \
                         r"|intl\.|co\.|<co>|corp\.|<corp>|\(tm\)|\(r\)|®|\(rev ..\)|\'|\"|\sinc\s*$|@|cpu |cpu deca" \
                         r"|([0-9]+|single|dual|two|triple|three|tri|quad|four|penta|five|hepta|six|hexa|seven|octa" \
                         r"|eight|multi)[ -]core|ennea|genuine|multi|processor|single|triple|[0-9\.]+ *[MmGg][Hh][Zz]"


@singleton
class ProcCpuinfoRepository:
    @inject
    def __init__(self) -> None:
        self._lock = threading.RLock()

    cpu_info_mapping = {
        'processor_id': [int, 'processor'],
        'vendor_id': [str, 'vendor_id'],
        'specification': [str, 'model name'],
        'family': [int, 'cpu family'],
        'model': [int, 'model'],
        'stepping': [int, 'stepping'],
        'microcode': [str, 'microcode'],
        'core_speed': [float, 'cpu MHz', 'cpu speed', 'clock'],
        'physical_package_id': [int, 'physical id'],
        'threads': [int, 'siblings'],
        'core_id': [int, 'core id'],
        'cores': [int, 'cpu cores'],
        'flags': [str, 'flags'],
        'bugs': [str, 'bugs'],
        'bogomips': [float, 'bogomips'],
    }

    @synchronized_with_attr("_lock")
    def refresh(self, system_info: SystemInfo) -> SystemInfo:
        if not os.path.exists(PATH_PROC_CPUINFO):
            _LOG.warning("%s not found", PATH_PROC_CPUINFO)
            return system_info

        try:
            with open(PATH_PROC_CPUINFO, 'r') as file:
                output = file.read()
        except IOError:
            _LOG.exception("Error while reading %s", PATH_PROC_CPUINFO)
            return system_info

        # load data on a temp variable
        temp_processor_list: List[Processor] = []
        tmp_proc: Optional[Processor] = None
        for line in output.splitlines():
            if ':' in line:
                label, value = line.split(':', 1)
                label = label.strip()
                value = value.strip()
                if label in self.cpu_info_mapping['processor_id'][1:]:
                    tmp_proc = Processor()
                    temp_processor_list.append(tmp_proc)
                self._parse_data(label, tmp_proc, value)

        # needed to avoid adding twice cpus with same core_id (Hyperthreading/SMT)
        clock_dict: Dict[int, Dict[int, bool]] = {}

        for tmp_proc in temp_processor_list:
            # get final variable
            processor = system_info.cpu_info.get_processor(tmp_proc.get_selected_processor())
            clock = tmp_proc.core_speed
            if clock is not None:
                clock_package = clock_dict.get(tmp_proc.physical_package_id)
                if clock_package is None:
                    clock_package = {}
                    clock_dict[tmp_proc.physical_package_id] = clock_package
                if clock_package.get(tmp_proc.core_id) is None:
                    clock_package[tmp_proc.core_id] = True
                    item = MonitoredItem(
                        str(tmp_proc.core_id),
                        f"Core #{tmp_proc.core_id}",
                        round(tmp_proc.core_speed),
                        FeatureType.CLOCK
                    )
                    system_info.cpu_info.set_clock_monitored_item(tmp_proc.physical_package_id, item)
            for attr, value in tmp_proc.__dict__.items():
                if value is not None:
                    processor.__setattr__(attr, value)

        return system_info

    def _parse_data(self, label: str, temp_processor: Processor, value: str) -> None:
        for name, labels in self.cpu_info_mapping.items():
            if label in labels[1:] and value:
                if name == 'core_speed':
                    temp_processor.core_speed = float(value) * 1000 * 1000
                elif name == 'flags':
                    temp_processor.flags = sorted(value.strip().split())
                elif name == 'bugs':
                    temp_processor.bugs = sorted(value.strip().split())
                else:
                    if name == 'specification':
                        temp_processor.name = self.clean_cpu_string(value)
                    value = labels[0](value)
                    temp_processor.__setattr__(name, value)

    @staticmethod
    def clean_cpu_string(specification: str) -> str:
        return ' '.join(re.sub(CLEAN_CPU_STRING_REGEX, '', specification, flags=re.IGNORECASE).split())
