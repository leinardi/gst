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
import threading
from typing import List

import humanfriendly
from injector import singleton, inject

from gst.model.cache import Cache
from gst.model.system_info import SystemInfo
from gst.repository.stress_ng_repository import PATH_SYS_SYSTEM
from gst.util.concurrency import synchronized_with_attr

PATH_SYS_CPU = PATH_SYS_SYSTEM + "/cpu"
_LOG = logging.getLogger(__name__)


@singleton
class SysDevicesCacheRepository:
    @inject
    def __init__(self) -> None:
        self._lock = threading.RLock()

    @staticmethod
    def _has_sys_devices_cache() -> bool:
        return os.path.exists(os.path.join(PATH_SYS_CPU, "cpu0", "cache"))

    @synchronized_with_attr("_lock")
    def refresh(self, system_info: SystemInfo) -> SystemInfo:
        if not self._has_sys_devices_cache():
            _LOG.warning("%s not found", os.path.join(PATH_SYS_CPU, "cpu0", "cache"))
            return system_info

        for physical in system_info.cpu_info.physical_package_id_list:
            cache_list: List[Cache] = []
            for _, processor in physical.items():
                cache_path = os.path.join(PATH_SYS_CPU, "cpu%s" % processor.processor_id, "cache")
                n_caches = 0
                while os.path.exists(
                        os.path.join(cache_path, "index%d" % n_caches)):
                    n_caches += 1
                if not n_caches:
                    continue

                self._read_cache_info(cache_list, cache_path, n_caches)

            cache_l1_data, cache_l1_inst, cache_l2, cache_l3 \
                = self._update_cache_count(cache_list)

            for _, processor in physical.items():
                processor.cache_l1_data = cache_l1_data
                processor.cache_l1_inst = cache_l1_inst
                processor.cache_l2 = cache_l2
                processor.cache_l3 = cache_l3
        return system_info

    @staticmethod
    def _read_cache_info(cache_list, cache_path, n_caches):
        for i in range(n_caches):
            cache = Cache()
            index_path = os.path.join(cache_path, "index%d" % i)
            with open(os.path.join(index_path, "id"), 'r') as file:
                cache.id = int(file.read().strip())
            with open(os.path.join(index_path, "level"), 'r') as file:
                cache.level = int(file.read().strip())
            with open(os.path.join(index_path, "number_of_sets"), 'r') as file:
                cache.number_of_sets = int(file.read().strip())
            with open(os.path.join(index_path, os.pardir, os.pardir, "topology", "physical_package_id"), 'r') as file:
                cache.physical_package_id = int(file.read().strip())
            with open(os.path.join(index_path, "size"), 'r') as file:
                cache.size = humanfriendly.parse_size(file.read().strip(), True)
            with open(os.path.join(index_path, "type"), 'r') as file:
                cache.type = file.read().strip()
            with open(os.path.join(index_path, "ways_of_associativity"), 'r') as file:
                cache.ways_of_associativity = int(file.read().strip())
            if cache not in cache_list:
                cache_list.append(cache)

    @staticmethod
    def _update_cache_count(cache_list):
        cache_l1_data: Cache = None
        cache_l1_inst: Cache = None
        cache_l2: Cache = None
        cache_l3: Cache = None
        for cache in cache_list:
            if cache.level == 1:
                if cache.type == 'Data':
                    if not cache_l1_data:
                        cache_l1_data = cache
                    cache_l1_data.count += 1
                elif cache.type == 'Instruction':
                    if not cache_l1_inst:
                        cache_l1_inst = cache
                    cache_l1_inst.count += 1
            elif cache.level == 2:
                if not cache_l2:
                    cache_l2 = cache
                cache_l2.count += 1
            elif cache.level == 3:
                if not cache_l3:
                    cache_l3 = cache
                cache_l3.count += 1
        return cache_l1_data, cache_l1_inst, cache_l2, cache_l3
