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
from typing import List

from injector import singleton, inject

from gst.model.cpu_info import CpuInfo
from gst.model.cpu_usage import CpuUsage
from gst.model.hardware_monitor import HardwareMonitor
from gst.model.load_avg import LoadAvg
from gst.model.mem_usage import MemUsage
from gst.model.memory_bank_info import MemoryBankInfo
from gst.model.mobo_info import MoboInfo


@singleton
class SystemInfo:
    @inject
    def __init__(self) -> None:
        self.cpu_info: CpuInfo = CpuInfo()
        self.mobo_info: MoboInfo = MoboInfo()
        self.memory_bank_info_list: List[MemoryBankInfo] = [MemoryBankInfo()]
        self.cpu_usage: CpuUsage = CpuUsage()
        self.mem_usage: MemUsage = MemUsage()
        self.load_avg: LoadAvg = LoadAvg()
        self.hwmon: HardwareMonitor = HardwareMonitor()
