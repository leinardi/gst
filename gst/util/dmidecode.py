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

# Original code from https://github.com/zaibon/py-dmidecode

import re
from enum import IntEnum
from typing import Dict, List, Union


class DmiType(IntEnum):
    BIOS = 0
    SYSTEM = 1
    BASEBOARD = 2
    CHASSIS = 3
    PROCESSOR = 4
    MEMORY_CONTROLLER = 5
    MEMORY_MODULE = 6
    CACHE = 7
    PORT_CONNECTOR = 8
    SYSTEM_SLOTS = 9
    ON_BOARD_DEVICES = 10
    OEM_STRINGS = 11
    SYSTEM_CONFIGURATION_OPTIONS = 12
    BIOS_LANGUAGE = 13
    GROUP_ASSOCIATIONS = 14
    SYSTEM_EVENT_LOG = 15
    PHYSICAL_MEMORY_ARRAY = 16
    MEMORY_DEVICE = 17
    MEMORY_ERROR_32_BIT = 18
    MEMORY_ARRAY_MAPPED_ADDRESS = 19
    MEMORY_DEVICE_MAPPED_ADDRESS = 20
    BUILT_IN_POINTING_DEVICE = 21
    PORTABLE_BATTERY = 22
    SYSTEM_RESET = 23
    HARDWARE_SECURITY = 24
    SYSTEM_POWER_CONTROLS = 25
    VOLTAGE_PROBE = 26
    COOLING_DEVICE = 27
    TEMPERATURE_PROBE = 28
    ELECTRICAL_CURRENT_PROBE = 29
    OUT_OF_BAND_REMOTE_ACCESS = 30
    BOOT_INTEGRITY_SERVICES = 31
    SYSTEM_BOOT = 32
    MEMORY_ERROR_64_BIT = 33
    MANAGEMENT_DEVICE = 34
    MANAGEMENT_DEVICE_COMPONENT = 35
    MANAGEMENT_DEVICE_THRESHOLD_DATA = 36
    MEMORY_CHANNEL = 37
    IPMI_DEVICE = 38
    POWER_SUPPLY = 39
    ADDITIONAL_INFORMATION = 40
    ONBOARD_DEVICES_EXTENDED_INFORMATION = 41
    MANAGEMENT_CONTROLLER_HOST_INTERFACE = 42


class DmiParse:
    def __init__(self, text_output: str) -> None:
        self.dmi_data: Dict[str, Dict[str, Union[str, int]]] = {}
        self._parse(text_output)

    def get_type(self, dmi_type: int) -> List[Dict]:
        result: List[Dict[str, Union[str, int]]] = []
        for entry in self.dmi_data.values():
            if entry['DMIType'] == dmi_type:
                result.append(entry)
        return result

    handle_re = re.compile('^Handle\\s+(.+),\\s+DMI\\s+type\\s+(\\d+),\\s+(\\d+)\\s+bytes$')
    in_block_re = re.compile("^\\t\\t(.+)$")
    record_re = re.compile("\\t(.+):\\s+(.+)$")
    record2_re = re.compile("\\t(.+):$")

    def _parse(self, text_output: str) -> None:
        #  Each record is separated by double newlines
        split_output = text_output.split('\n\n')

        for record in split_output:
            record_element = record.splitlines()

            #  Entries with less than 3 lines are incomplete / inactive; skip them
            if len(record_element) < 3:
                continue

            handle_data = DmiParse.handle_re.findall(record_element[0])

            if not handle_data:
                continue
            handle_data = handle_data[0]

            dmi_handle = handle_data[0]

            self.dmi_data[dmi_handle] = {}
            self.dmi_data[dmi_handle]["DMIType"] = int(handle_data[1])
            self.dmi_data[dmi_handle]["DMISize"] = int(handle_data[2])

            #  Okay, we know 2nd line == name
            self.dmi_data[dmi_handle]["DMIName"] = record_element[1]

            in_block_element = ""
            in_block_list = ""

            #  Loop over the rest of the record, gathering values
            for i in range(2, len(record_element), 1):
                if i >= len(record_element):
                    break
                #  Check whether we are inside a \t\t block
                if in_block_element != "":

                    in_block_data = DmiParse.in_block_re.findall(record_element[1])

                    if in_block_data:
                        if not in_block_list:
                            in_block_list = in_block_data[0][0]
                        else:
                            in_block_list = f"{in_block_list}\t\t{in_block_data[0][1]}"

                        self.dmi_data[dmi_handle][in_block_element] = in_block_list
                        continue
                    else:
                        # We are out of the \t\t block; reset it again, and let
                        # the parsing continue
                        in_block_element = ""

                record_data = DmiParse.record_re.findall(record_element[i])

                #  Is this the line containing handle identifier, type, size?
                if record_data:
                    self.dmi_data[dmi_handle][record_data[0][0]] = record_data[0][1]  # noq
                    continue

                #  Didn't findall regular entry, maybe an array of data?
                record_data2 = DmiParse.record2_re.findall(record_element[i])

                if record_data2:
                    #  This is an array of data - let the loop know we are inside
                    #  an array block
                    in_block_element = record_data2[0][0]
                    continue
