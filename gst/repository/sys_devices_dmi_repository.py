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

from injector import singleton, inject

from gst.model.system_info import SystemInfo
from gst.util.concurrency import synchronized_with_attr

_LOG = logging.getLogger(__name__)
PATH_SYS_DEVICE_VIRTUAL = "/sys/devices/virtual"
PATH_SYS_VIRTUAL_DMI = PATH_SYS_DEVICE_VIRTUAL + "/dmi/id"


@singleton
class SysDevicesDmiRepository:
    @inject
    def __init__(self) -> None:
        self._lock = threading.RLock()

    @staticmethod
    def _has_sys_devices_dmi() -> bool:
        return os.path.exists(PATH_SYS_VIRTUAL_DMI)

    @synchronized_with_attr("_lock")
    def refresh(self, system_info: SystemInfo) -> SystemInfo:
        if not self._has_sys_devices_dmi():
            _LOG.warning("%s not found", PATH_SYS_VIRTUAL_DMI)
            return system_info

        for attr, _ in system_info.mobo_info:
            try:
                with open(os.path.join(PATH_SYS_VIRTUAL_DMI, attr), 'r') as file:
                    file_content = file.read().strip()
                    system_info.mobo_info.__setattr__(attr, file_content if file_content else None)
            except PermissionError:
                pass

        return system_info
