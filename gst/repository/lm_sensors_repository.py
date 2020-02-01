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
from typing import List, Optional

from injector import singleton, inject

from gst.model.monitored_item import MonitoredItem
from gst.model.system_info import SystemInfo
from gst.util import sensors
from gst.util.concurrency import synchronized_with_attr
from gst.util.sensors import FeatureType

_LOG = logging.getLogger(__name__)
_SHORT_NAME_AVERAGE = 'average'
_SHORT_NAME_INPUT = 'input'
_SENSOR_MIN_TEMP = -127
_SENSOR_MAX_TEMP = 215


@singleton
class LmSensorsRepository:
    @inject
    def __init__(self) -> None:
        self._lock = threading.RLock()

    @synchronized_with_attr("_lock")
    def refresh(self, system_info: SystemInfo) -> SystemInfo:
        sensors.init()
        for chip in sensors.ChipIterator():
            chip_name = sensors.chip_snprintf_name(chip)
            for feature in sensors.FeatureIterator(chip):
                subfeatures = list(sensors.SubFeatureIterator(chip, feature))  # get a list of all subfeatures

                item_id = feature.name.decode("utf-8")
                item_name = sensors.get_label(chip, feature)
                item_value: Optional[float] = None
                item_average_value: Optional[float] = None
                item_type = sensors.FeatureType(feature.type)

                skipname = len(feature.name) + 1  # skip common prefix
                additional_values: List[str] = []
                for subfeature in subfeatures:
                    short_name = subfeature.name[skipname:].decode("utf-8")
                    try:
                        value = sensors.get_value(chip, subfeature.number)
                    except Exception:
                        _LOG.warning(
                            f"Unable to read "
                            f"{chip.path.decode('utf-8')}/{subfeature.name.decode('utf-8')} ({chip_name})")
                        value = None
                    if short_name == _SHORT_NAME_INPUT:
                        item_value = self._filter_value(item_type, item_value, value)
                    elif short_name == _SHORT_NAME_AVERAGE:
                        item_average_value = self._filter_value(item_type, item_average_value, value)
                    else:
                        self._add_additional_value(additional_values, short_name, value)

                if item_value is None:
                    item_value = item_average_value
                elif item_average_value is not None:
                    self._add_additional_value(additional_values, _SHORT_NAME_AVERAGE, item_average_value)

                if additional_values:
                    item_name = "{} ({})".format(item_name, ", ".join(additional_values))
                item = MonitoredItem(item_id, item_name, item_value, item_type)
                system_info.hwmon.set_hw_monitored_item(chip_name, item)
        sensors.cleanup()
        return system_info

    @staticmethod
    def _filter_value(feature_type: FeatureType, item: Optional[float], value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if feature_type == FeatureType.TEMP:
            item = value if _SENSOR_MIN_TEMP < value < _SENSOR_MAX_TEMP else None
        else:
            item = value
        return item

    @staticmethod
    def _add_additional_value(additional_values: List[str], short_name: str, value: float) -> None:
        formatted_value = "{:.2f}".format(value).rstrip('0').rstrip('.')
        additional_values.append(f"{short_name}: {formatted_value}")
