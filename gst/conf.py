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
from typing import Dict, Any

APP_PACKAGE_NAME = "gst"
APP_NAME = "GST"
APP_ID = "com.leinardi.gst"
APP_VERSION = "0.7.5"
APP_ICON_NAME = APP_ID
APP_ICON_NAME_SYMBOLIC = APP_ID + "-symbolic"
APP_DB_NAME = APP_PACKAGE_NAME + ".db"
APP_MAIN_UI_NAME = "main.glade"
APP_PREFERENCES_UI_NAME = "preferences.glade"
APP_DESKTOP_ENTRY_NAME = APP_PACKAGE_NAME + ".desktop"
APP_DESCRIPTION = 'GTK stress and monitoring utility'
APP_SOURCE_URL = 'https://gitlab.com/leinardi/gst'
APP_AUTHOR = 'Roberto Leinardi'
APP_AUTHOR_EMAIL = 'roberto@leinardi.com'

SETTINGS_DEFAULTS: Dict[str, Any] = {
    'settings_check_new_version': False,
    'settings_refresh_interval': 2,
}

DESKTOP_ENTRY: Dict[str, str] = {
    'Type': 'Application',
    'Encoding': 'UTF-8',
    'Name': APP_NAME,
    'Comment': APP_DESCRIPTION,
    'Terminal': 'false',
    'Categories': 'System;Settings;',
}
