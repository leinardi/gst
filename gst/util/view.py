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

from typing import Optional, Any, List

import humanfriendly
from gi.repository import GLib, Gtk, Gdk

from gst.model.cache import Cache
from gst.util.sensors import FeatureType


def build_glib_option(long_name: str,
                      short_name: Optional[str] = None,
                      flags: int = 0,
                      arg: int = GLib.OptionArg.NONE,
                      arg_data: Optional[object] = None,
                      description: Optional[str] = None,
                      arg_description: Optional[str] = None) -> GLib.OptionEntry:
    option = GLib.OptionEntry()
    option.long_name = long_name
    option.short_name = 0 if not short_name else ord(short_name[0])
    option.flags = flags
    option.description = description
    option.arg = arg
    option.arg_description = arg_description
    option.arg_data = arg_data
    return option


def hide_on_delete(widget: Gtk.Widget, *_: Any) -> Any:
    widget.hide()
    return widget.hide_on_delete()


def rgba_to_hex(color: Gdk.RGBA) -> str:
    """Return hexadecimal string for :class:`Gdk.RGBA` `color`."""
    return "#{0:02x}{1:02x}{2:02x}{3:02x}".format(int(color.red * 255),
                                                  int(color.green * 255),
                                                  int(color.blue * 255),
                                                  int(color.alpha * 255))


def is_dazzle_version_supported() -> bool:
    if Gtk.MAJOR_VERSION >= 3 and Gtk.MINOR_VERSION >= 24:  # Mypy says that this check returns Any, not sure why...
        return True
    return False


def get_default_application() -> Gtk.Application:
    return Gtk.Application.get_default()


def open_uri(uri: str, parent: Gtk.Window = None, timestamp: int = Gdk.CURRENT_TIME) -> None:
    Gtk.show_uri_on_window(parent, uri, timestamp)


# pylint: disable=too-many-branches,too-many-statements
def filter_flags(flags: Optional[List[str]]) -> Optional[str]:
    if not flags:
        return None
    filtered_flags: List[str] = []
    if "mmx" in flags:
        filtered_flags.append("MMX")
    if "mmxext" in flags:
        filtered_flags.append("(+)")
    if "3dnow" in flags:
        filtered_flags.append("3DNOW!")
    if "3dnowext" in flags:
        filtered_flags.append("(+)")
    if "sse" in flags:
        filtered_flags.append("SSE(1")
    if "sse2" in flags:
        filtered_flags.append("2")
    if "pni" in flags:
        filtered_flags.append("3")
    if "ssse3" in flags:
        filtered_flags.append("3S")
    if "sse4_1" in flags:
        filtered_flags.append("4.1")
    if "sse4_2" in flags:
        filtered_flags.append("4.2")
    if "sse4a" in flags:
        filtered_flags.append("4A")
    if "sse" in flags:
        filtered_flags.append(")")
    if "xop" in flags:
        filtered_flags.append("XOP")
    if "avx" in flags:
        filtered_flags.append("AVX(1")
    if "avx2" in flags:
        filtered_flags.append("2")
    if "avx512f" in flags:
        filtered_flags.append("512")
    if "avx" in flags:
        filtered_flags.append(")")
    if "fma3" in flags:
        filtered_flags.append("FMA(3")
    if "fma4" in flags:
        filtered_flags.append("4")
    if "fma3" in flags:
        filtered_flags.append(")")
    # Security and Cryptography
    if "aes" in flags:
        filtered_flags.append("AES")
    if "pclmulqdq" in flags:
        filtered_flags.append("CLMUL")
    if "rdrand" in flags:
        filtered_flags.append("RdRand")
    if "sha_ni" in flags:
        filtered_flags.append("SHA")
    if "sgx" in flags:
        filtered_flags.append("SGX")
    # Virtualization
    if "vmx" in flags:
        filtered_flags.append("VT-x")
    if "svm" in flags:
        filtered_flags.append("AMD-V")
    # Other
    if "lm" in flags:
        filtered_flags.append("x86-64")

    if filtered_flags:
        return ', '.join(filtered_flags).replace(', )', ')')  # not proud of this replace :(
    return None


def format_hex(value: Optional[int]) -> Optional[str]:
    return "%d (%sh)" % (value, format(value, 'x').upper()) if value is not None else None


def format_frequency(value: Optional[float], show_always_mhz: bool = True) -> Optional[str]:
    if not value:
        return None
    if show_always_mhz:
        return f"{round(value / (1000 * 1000))} MHz"
    return humanfriendly.format_size(value, binary=False).replace('byte', 'hertz').replace('B', 'Hz')


def format_power(value: Optional[float]) -> Optional[str]:
    return humanfriendly.format_size(value, binary=False) \
        .replace('bytes', 'W') \
        .replace('byte', 'W') \
        .replace('B', 'W') \
        if value else None


def format_size(value: Optional[int]) -> Optional[str]:
    return humanfriendly.format_size(value, binary=True) if value else None


def format_length(value: Optional[float]) -> Optional[str]:
    return humanfriendly.format_length(value) if value else None


def format_cache_size(cache: Optional[Cache]) -> Optional[str]:
    return ("%d x %s (%s)" % (
        cache.count,
        format_size(cache.size),
        format_size(cache.count * cache.size))) if cache and cache.count and cache.size else None


def format_cache_ways(cache: Optional[Cache]) -> Optional[str]:
    return ("%d-way" % cache.ways_of_associativity) if cache and cache.ways_of_associativity else None


def format_cache_sets(cache: Optional[Cache]) -> Optional[str]:
    return ("%d sets" % cache.number_of_sets) if cache and cache.number_of_sets else None


def format_feature_type_value(value: Optional[float], feature_type: FeatureType) -> str:
    if value is None:
        return "N/A"
    if feature_type == FeatureType.IN:
        return f"{value:.3f} V"
    if feature_type == FeatureType.FAN:
        return f"{round(value)} RPM"
    if feature_type == FeatureType.TEMP:
        return f"{round(value)} °C"
    if feature_type == FeatureType.POWER:
        return f"{value:.1f} W"
    if feature_type == FeatureType.ENERGY:
        return f"{value:.1f} J"
    if feature_type == FeatureType.CURR:
        return f"{value:.1f} A"
    if feature_type == FeatureType.HUMIDITY:
        return f"{round(value)} %"
    if feature_type == FeatureType.INTRUSION:
        return f"{value}"
    if feature_type == FeatureType.BEEP_ENABLE:
        return f"{value}"
    if feature_type == FeatureType.CLOCK:
        return f"{round(value)} Hz"
    return "Unknown"


def get_sensors_feature_type_name(feature_type: FeatureType) -> str:
    if feature_type == FeatureType.IN:
        return "⚡ Voltages"
    if feature_type == FeatureType.FAN:
        return "🌀 Fans"
    if feature_type == FeatureType.TEMP:
        return "🌡️ Temperatures"
    if feature_type == FeatureType.POWER:
        return "⚡ Power"
    if feature_type == FeatureType.ENERGY:
        return "⚡ Energy"
    if feature_type == FeatureType.CURR:
        return "⚡ Currents"
    if feature_type == FeatureType.HUMIDITY:
        return "💧 Humidity"
    if feature_type == FeatureType.INTRUSION:
        return "🚨 Intrusion detection"
    if feature_type == FeatureType.BEEP_ENABLE:
        return "Bitmask for beep"
    if feature_type == FeatureType.CLOCK:
        return "Voltages"
    return "Unknown"
