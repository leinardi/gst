#!/usr/bin/env python3

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
import signal
import locale
import gettext
import logging
import sys
from types import TracebackType
from typing import Type
from os.path import abspath, join, dirname
from peewee import SqliteDatabase
from gi.repository import GLib
from rx.disposable import CompositeDisposable

from gst.conf import APP_PACKAGE_NAME
from gst.model.setting import Setting
from gst.repository.stress_ng_repository import StressNgRepository
from gst.util.log import set_log_level
from gst.di import INJECTOR
from gst.app import Application

WHERE_AM_I = abspath(dirname(__file__))
LOCALE_DIR = join(WHERE_AM_I, 'mo')

set_log_level(logging.INFO)

_LOG = logging.getLogger(__name__)

# POSIX locale settings
locale.setlocale(locale.LC_ALL, locale.getlocale())
locale.bindtextdomain(APP_PACKAGE_NAME, LOCALE_DIR)

gettext.bindtextdomain(APP_PACKAGE_NAME, LOCALE_DIR)
gettext.textdomain(APP_PACKAGE_NAME)


def _cleanup() -> None:
    try:
        _LOG.debug("cleanup")
        INJECTOR.get(StressNgRepository).terminate()
        INJECTOR.get(CompositeDisposable).dispose()
        INJECTOR.get(SqliteDatabase).close()
        # futures.thread._threads_queues.clear()
    except:
        _LOG.exception("Error during cleanup!")


def handle_exception(type_: Type[BaseException], value: BaseException, traceback: TracebackType) -> None:
    if issubclass(type_, KeyboardInterrupt):
        sys.__excepthook__(type_, value, traceback)
        return

    _LOG.critical("Uncaught exception", exc_info=(type_, value, traceback))
    _cleanup()
    sys.exit(1)


sys.excepthook = handle_exception


def _init_database() -> None:
    database = INJECTOR.get(SqliteDatabase)
    database.create_tables([
        Setting
    ])


def main() -> int:
    _LOG.debug("main")
    _init_database()
    application: Application = INJECTOR.get(Application)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, application.quit)
    exit_status = application.run(sys.argv)
    _cleanup()
    return sys.exit(exit_status)


if __name__ == "__main__":
    main()
