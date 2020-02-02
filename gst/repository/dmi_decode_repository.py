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
import threading
from enum import Enum, auto
from typing import Dict, Optional

from injector import singleton, inject

from gst.model.system_info import SystemInfo, MemoryBankInfo
from gst.util.concurrency import synchronized_with_attr
from gst.util.dmidecode import DmiParse, DmiType
from gst.util.linux import is_root
from gst.util.subprocess import run_on_host_and_get_stdout, check_if_command_is_available

_LOG = logging.getLogger(__name__)


class DmiDecodeRepositoryResult(Enum):
    SUCCESS = auto()
    ERROR_DMI_DECODE_NOT_AVAILABLE = auto()
    ERROR_GENERIC = auto()


@singleton
class DmiDecodeRepository:
    @inject
    def __init__(self) -> None:
        self._lock = threading.RLock()

    @synchronized_with_attr("_lock")
    def refresh(self, system_info: SystemInfo) -> DmiDecodeRepositoryResult:
        cmd = ['dmidecode']

        if not check_if_command_is_available(cmd[0], True):
            return DmiDecodeRepositoryResult.ERROR_DMI_DECODE_NOT_AVAILABLE

        if not is_root():
            cmd.insert(0, 'pkexec')
        result = run_on_host_and_get_stdout(cmd)
        _LOG.debug(f"Exit code: {result[0]}. {result[1]}\n{result[2]}")

        if result[0] != 0:
            _LOG.error(f"Error executing dmidecode (exit code {result[0]}): {result[2]}")
            return DmiDecodeRepositoryResult.ERROR_GENERIC

        dmi = DmiParse(result[1])
        dmi_entry_list = dmi.get_type(DmiType.MEMORY_DEVICE.value)
        memory_bank_info_list = []
        for entry in dmi_entry_list:
            mem_info = MemoryBankInfo()
            mem_info.locator = self._get_entry_value('Locator', entry)
            mem_info.bank_locator = self._get_entry_value('Bank Locator', entry)
            mem_info.type = self._get_entry_value('Type', entry)
            mem_info.type_detail = self._get_entry_value('Type Detail', entry)
            mem_info.size = self._get_entry_value('Size', entry)
            mem_info.speed = self._get_entry_value('Speed', entry)
            mem_info.rank = self._get_entry_value('Rank', entry)
            mem_info.manufacturer = self._get_entry_value('Manufacturer', entry)
            mem_info.part_number = self._get_entry_value('Part Number', entry)
            memory_bank_info_list.append(mem_info)
        if memory_bank_info_list:
            system_info.memory_bank_info_list = memory_bank_info_list

        dmi_entry_list = dmi.get_type(DmiType.PROCESSOR.value)
        for entry in dmi_entry_list:
            package = self._get_entry_value('Upgrade', entry)
            if package is not None:
                signature = self._get_entry_value('Signature', entry)
                if signature is not None:
                    signature_list = signature.split(',')
                    family = 0
                    model = 0
                    stepping = 0
                    for s in signature_list:
                        s_lower = s.lower().strip()
                        if 'family' in s_lower:
                            family = int(s_lower.split(' ')[1])
                        if 'model' in s_lower:
                            model = int(s_lower.split(' ')[1])
                        if 'stepping' in s_lower:
                            stepping = int(s_lower.split(' ')[1])
                    for ppi in system_info.cpu_info.physical_package_id_list:
                        for processor in ppi.values():
                            if processor.family == family \
                                    and processor.model == model \
                                    and processor.stepping == stepping:
                                processor.package = package
        return DmiDecodeRepositoryResult.SUCCESS

    @staticmethod
    def _get_entry_value(key: str, entry: Dict) -> Optional[str]:
        value = entry.get(key)
        return value if value != 'Unknown' else None
