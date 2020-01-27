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
from typing import NewType

from gi.repository import Gtk
from injector import Module, provider, singleton, Injector
from peewee import SqliteDatabase
from rx.disposable import CompositeDisposable
from rx.subject import Subject

from gst.conf import APP_PACKAGE_NAME, APP_MAIN_UI_NAME, APP_DB_NAME, APP_PREFERENCES_UI_NAME
from gst.util.path import get_config_path

_LOG = logging.getLogger(__name__)

MainBuilder = NewType('MainBuilder', Gtk.Builder)
EditFanProfileBuilder = NewType('EditFanProfileBuilder', Gtk.Builder)
EditOverclockProfileBuilder = NewType('EditOverclockProfileBuilder', Gtk.Builder)
HistoricalDataBuilder = NewType('HistoricalDataBuilder', Gtk.Builder)
PreferencesBuilder = NewType('PreferencesBuilder', Gtk.Builder)

_UI_RESOURCE_PATH = "/com/leinardi/gst/ui/{}"


# pylint: disable=no-self-use
class ProviderModule(Module):
    @singleton
    @provider
    def provide_main_builder(self) -> MainBuilder:
        _LOG.debug("provide Gtk.Builder")
        builder = MainBuilder(Gtk.Builder())
        builder.set_translation_domain(APP_PACKAGE_NAME)
        builder.add_from_resource(_UI_RESOURCE_PATH.format(APP_MAIN_UI_NAME))
        return builder

    @singleton
    @provider
    def provide_preferences_builder(self) -> PreferencesBuilder:
        _LOG.debug("provide Gtk.Builder")
        builder = PreferencesBuilder(Gtk.Builder())
        builder.set_translation_domain(APP_PACKAGE_NAME)
        builder.add_from_resource(_UI_RESOURCE_PATH.format(APP_PREFERENCES_UI_NAME))
        return builder

    @singleton
    @provider
    def provide_thread_pool_scheduler(self) -> CompositeDisposable:
        _LOG.debug("provide CompositeDisposable")
        return CompositeDisposable()

    @singleton
    @provider
    def provide_database(self) -> SqliteDatabase:
        _LOG.debug("provide SqliteDatabase")
        database = SqliteDatabase(get_config_path(APP_DB_NAME))
        database.connect()
        return database


INJECTOR = Injector(ProviderModule)
