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
import threading

import psutil
from injector import singleton, inject

from gst.model.system_info import SystemInfo
from gst.util.concurrency import synchronized_with_attr


@singleton
class PsUtilRepository:
    @inject
    def __init__(self) -> None:
        self._lock = threading.RLock()

    @synchronized_with_attr("_lock")
    def refresh(self, system_info: SystemInfo) -> SystemInfo:
        system_info.cpu_usage.cores = psutil.cpu_percent(percpu=True)
        cpu_times_percent = psutil.cpu_times_percent()
        system_info.cpu_usage.user = cpu_times_percent.user
        system_info.cpu_usage.nice = cpu_times_percent.nice
        system_info.cpu_usage.system = cpu_times_percent.system
        system_info.cpu_usage.io_wait = cpu_times_percent.iowait
        system_info.cpu_usage.irq = cpu_times_percent.irq
        system_info.cpu_usage.soft_irq = cpu_times_percent.softirq
        system_info.cpu_usage.steal = cpu_times_percent.steal
        system_info.cpu_usage.guest = cpu_times_percent.guest
        system_info.cpu_usage.guest_nice = cpu_times_percent.guest_nice
        system_info.load_avg.load_avg_1, system_info.load_avg.load_avg_5, system_info.load_avg.load_avg_15 \
            = psutil.getloadavg()
        system_info.load_avg.cpu_count = psutil.cpu_count()
        virtual_memory = psutil.virtual_memory()
        system_info.mem_usage.total = virtual_memory.total
        system_info.mem_usage.available = virtual_memory.available
        system_info.mem_usage.percent = virtual_memory.percent
        return system_info