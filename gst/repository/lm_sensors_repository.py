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
from typing import List

from injector import singleton, inject

from gst.model.monitored_item import MonitoredItem
from gst.model.system_info import SystemInfo
from gst.util import sensors
from gst.util.concurrency import synchronized_with_attr

LOG = logging.getLogger(__name__)


@singleton
class LmSensorsRepository:
    @inject
    def __init__(self) -> None:
        self._lock = threading.RLock()

    @synchronized_with_attr("_lock")
    def refresh(self, system_info: SystemInfo) -> SystemInfo:
        sensors.init()
        LOG.debug(f"libsensor version: {sensors.VERSION}")
        for chip in sensors.ChipIterator():
            chip_name = sensors.chip_snprintf_name(chip)
            for feature in sensors.FeatureIterator(chip):
                subfeatures = list(sensors.SubFeatureIterator(chip, feature))  # get a list of all subfeatures

                item_id = feature.name.decode("utf-8")
                item_name = sensors.get_label(chip, feature)
                item_value = 0.0
                item_type = sensors.FeatureType(feature.type)

                skipname = len(feature.name) + 1  # skip common prefix
                additional_values: List[str] = []
                for subfeature in subfeatures:
                    short_name = subfeature.name[skipname:].decode("utf-8")
                    value = sensors.get_value(chip, subfeature.number)
                    if short_name == 'input':
                        item_value = value
                    else:
                        additional_values.append(f"{short_name}: {value}")

                if additional_values:
                    item_name = "{} ({})".format(item_name, ", ".join(additional_values))
                item = MonitoredItem(item_id, item_name, item_value, item_type)
                system_info.hwmon.set_hw_monitored_item(chip_name, item)
        sensors.cleanup()
        return system_info
