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

# Python Bindings for libsensors3
#
# use the documentation of libsensors for the low level API.
# see example.py for high level API usage.
#
# @author: Pavel Rojtberg (http://www.rojtberg.net)
# @see: https://github.com/paroj/sensors.py
# @copyright: LGPLv2 (same as libsensors) <http://opensource.org/licenses/LGPL-2.1>

import ctypes.util
import sys
from ctypes import cdll, c_void_p, c_char_p, Structure, c_short, c_int, c_uint, POINTER, byref, create_string_buffer, \
    cast, c_double
from enum import Enum, IntEnum, IntFlag
from typing import Tuple, Union, Optional

_LIBC = cdll.LoadLibrary(ctypes.util.find_library("c"))
# see https://github.com/paroj/sensors.py/issues/1
_LIBC.free.argtypes = [c_void_p]

_HDL = cdll.LoadLibrary(ctypes.util.find_library("sensors"))

VERSION = c_char_p.in_dll(_HDL, "libsensors_version").value.decode("ascii")


class SensorsError(Exception):
    pass


class ErrorWildcards(SensorsError):
    pass


class ErrorNoEntry(SensorsError):
    pass


class ErrorAccessRead(SensorsError, OSError):
    pass


class ErrorKernel(SensorsError, OSError):
    pass


class ErrorDivZero(SensorsError, ZeroDivisionError):
    pass


class ErrorChipName(SensorsError):
    pass


class ErrorBusName(SensorsError):
    pass


class ErrorParse(SensorsError):
    pass


class ErrorAccessWrite(SensorsError, OSError):
    pass


class ErrorIO(SensorsError, IOError):
    pass


class ErrorRecursion(SensorsError):
    pass


_ERR_MAP = {
    1: ErrorWildcards,
    2: ErrorNoEntry,
    3: ErrorAccessRead,
    4: ErrorKernel,
    5: ErrorDivZero,
    6: ErrorChipName,
    7: ErrorBusName,
    8: ErrorParse,
    9: ErrorAccessWrite,
    10: ErrorIO,
    11: ErrorRecursion
}


def raise_sensor_error(errno: int, message: str = '') -> None:
    raise _ERR_MAP[abs(errno)](message)


class BusId(Structure):
    _fields_ = [("type", c_short),
                ("nr", c_short)]


class ChipName(Structure):
    _fields_ = [("prefix", c_char_p),
                ("bus", BusId),
                ("addr", c_int),
                ("path", c_char_p)]


class Feature(Structure):
    _fields_ = [("name", c_char_p),
                ("number", c_int),
                ("type", c_int)]


class FeatureType(IntFlag):
    IN = 0x00
    FAN = 0x01
    TEMP = 0x02
    POWER = 0x03
    ENERGY = 0x04
    CURR = 0x05
    HUMIDITY = 0x06
    MAX_MAIN = 0x7
    VID = 0x10
    INTRUSION = 0x11
    MAX_OTHER = 0x12
    BEEP_ENABLE = 0x18
    CLOCK = sys.maxsize


class Subfeature(Structure):
    _fields_ = [("name", c_char_p),
                ("number", c_int),
                ("type", c_int),
                ("mapping", c_int),
                ("flags", c_uint)]


_HDL.sensors_get_detected_chips.restype = POINTER(ChipName)
_HDL.sensors_get_features.restype = POINTER(Feature)
_HDL.sensors_get_all_subfeatures.restype = POINTER(Subfeature)
_HDL.sensors_get_label.restype = c_void_p  # return pointer instead of str so we can free it
_HDL.sensors_get_adapter_name.restype = c_char_p  # docs do not say whether to free this or not
_HDL.sensors_strerror.restype = c_char_p

# RAW API
MODE_R = 1
MODE_W = 2
COMPUTE_MAPPING = 4


def init(cfg_file: str = None) -> None:
    file = _LIBC.fopen(cfg_file.encode("utf-8"), "r") if cfg_file is not None else None

    result = _HDL.sensors_init(file)
    if result != 0:
        raise_sensor_error(result, "sensors_init failed")

    if file is not None:
        _LIBC.fclose(file)


def cleanup() -> None:
    _HDL.sensors_cleanup()


def parse_chip_name(orig_name: str) -> ChipName:
    ret = ChipName()
    err = _HDL.sensors_parse_chip_name(orig_name.encode("utf-8"), byref(ret))

    if err < 0:
        raise_sensor_error(err, strerror(err))

    return ret


def strerror(errnum: int) -> str:
    return str(_HDL.sensors_strerror(errnum).decode("utf-8"))


def free_chip_name(chip: ChipName) -> None:
    _HDL.sensors_free_chip_name(byref(chip))


def get_detected_chips(match: Optional[Union[ChipName, str]], nr: int) -> Tuple[ChipName, int]:
    """
    @return: (chip, next nr to query)
    """
    _nr = c_int(nr)

    if match is not None:
        match = byref(match)

    chip = _HDL.sensors_get_detected_chips(match, byref(_nr))
    chip = chip.contents if bool(chip) else None
    return chip, _nr.value


def chip_snprintf_name(chip: ChipName, buffer_size: int = 200) -> str:
    """
    @param buffer_size defaults to the size used in the sensors utility
    """
    ret = create_string_buffer(buffer_size)
    err = _HDL.sensors_snprintf_chip_name(ret, buffer_size, byref(chip))

    if err < 0:
        raise_sensor_error(err, strerror(err))

    return ret.value.decode("utf-8")


def do_chip_sets(chip: ChipName) -> None:
    """
    @attention this function was not tested
    """
    err = _HDL.sensors_do_chip_sets(byref(chip))
    if err < 0:
        raise_sensor_error(err, strerror(err))


def get_adapter_name(bus: BusId) -> str:
    return str(_HDL.sensors_get_adapter_name(byref(bus)).decode("utf-8"))


def get_features(chip: ChipName, nr: int) -> Tuple[Feature, int]:
    """
    @return: (feature, next nr to query)
    """
    _nr = c_int(nr)
    feature = _HDL.sensors_get_features(byref(chip), byref(_nr))
    feature = feature.contents if bool(feature) else None
    return feature, _nr.value


def get_label(chip: ChipName, feature: Feature) -> str:
    ptr = _HDL.sensors_get_label(byref(chip), byref(feature))
    val = cast(ptr, c_char_p).value.decode("utf-8")
    _LIBC.free(ptr)
    return val


def get_all_subfeatures(chip: ChipName, feature: Feature, nr: int) -> Tuple[Subfeature, int]:
    """
    @return: (subfeature, next nr to query)
    """
    _nr = c_int(nr)
    subfeature = _HDL.sensors_get_all_subfeatures(byref(chip), byref(feature), byref(_nr))
    subfeature = subfeature.contents if bool(subfeature) else None
    return subfeature, _nr.value


def get_value(chip: ChipName, subfeature_nr: int) -> float:
    val = c_double()
    err = _HDL.sensors_get_value(byref(chip), subfeature_nr, byref(val))
    if err < 0:
        raise_sensor_error(err, strerror(err))
    return val.value


def set_value(chip: ChipName, subfeature_nr: int, value: float) -> None:
    """
    @attention this function was not tested
    """
    val = c_double(value)
    err = _HDL.sensors_set_value(byref(chip), subfeature_nr, byref(val))
    if err < 0:
        raise_sensor_error(err, strerror(err))


# Convenience API
class ChipIterator:
    def __init__(self, match: Optional[str] = None) -> None:
        self.match = parse_chip_name(match) if match is not None else None
        self.nr = 0

    def __iter__(self) -> 'ChipIterator':
        return self

    def __next__(self) -> ChipName:
        chip, self.nr = get_detected_chips(self.match, self.nr)

        if chip is None:
            raise StopIteration

        return chip

    def __del__(self) -> None:
        if self.match is not None:
            free_chip_name(self.match)

    def next(self) -> ChipName:  # python2 compatibility
        return self.__next__()


class FeatureIterator:
    def __init__(self, chip: ChipName) -> None:
        self.chip = chip
        self.nr = 0

    def __iter__(self) -> 'FeatureIterator':
        return self

    def __next__(self) -> Feature:
        feature, self.nr = get_features(self.chip, self.nr)

        if feature is None:
            raise StopIteration

        return feature

    def next(self) -> Feature:  # python2 compatibility
        return self.__next__()


class SubFeatureIterator:
    def __init__(self, chip: ChipName, feature: Feature) -> None:
        self.chip = chip
        self.feature = feature
        self.nr = 0

    def __iter__(self) -> 'SubFeatureIterator':
        return self

    def __next__(self) -> Subfeature:
        subfeature, self.nr = get_all_subfeatures(self.chip, self.feature, self.nr)

        if subfeature is None:
            raise StopIteration

        return subfeature

    def next(self) -> Subfeature:  # python2 compatibility
        return self.__next__()
