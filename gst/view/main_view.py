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
import datetime
import logging
import math
from typing import Optional, Any, Dict, List, Tuple

from injector import inject, singleton
from gi.repository import Gtk
from gst.di import MainBuilder
from gst.interactor.settings_interactor import SettingsInteractor
from gst.model import SelectedProcessor, CPU_FLAGS, CPU_BUGS
from gst.model.cpu_info import CpuInfo
from gst.model.memory_bank_info import MemoryBankInfo, LOCATOR_DEFAULT_TEXT
from gst.model.processor import Processor
from gst.model.stress_tests_result import StressTestsResult
from gst.model.system_info import SystemInfo
from gst.util.sensors import FeatureType
from gst.util.view import hide_on_delete, format_cache_size, format_cache_ways, format_cache_sets, format_frequency, \
    format_hex, filter_flags, get_sensors_feature_type_name, format_feature_type_value, format_size
from gst.view.preferences_view import PreferencesView
from gst.conf import APP_PACKAGE_NAME, APP_NAME, APP_VERSION, APP_SOURCE_URL
from gst.presenter.main_presenter import MainPresenter, MainViewInterface

_LOG = logging.getLogger(__name__)
_CORE_USAGE_MAX_PER_ROW = 16


@singleton
class MainView(MainViewInterface):

    @inject
    def __init__(self,
                 presenter: MainPresenter,
                 preferences_view: PreferencesView,
                 builder: MainBuilder,
                 settings_interactor: SettingsInteractor,
                 system_info: SystemInfo
                 ) -> None:
        _LOG.debug('init MainView')
        self._presenter: MainPresenter = presenter
        self._preferences_view = preferences_view
        self._presenter.main_view = self
        self._builder: Gtk.Builder = builder
        self._settings_interactor = settings_interactor
        self._system_info: SystemInfo = system_info
        self._first_refresh = True
        self._selected_processor: SelectedProcessor = [0, 0]
        self._selected_mem_bank = 0
        self._init_widgets()

    def _init_widgets(self) -> None:
        self._window: Gtk.ApplicationWindow = self._builder.get_object('application_window')
        self._preferences_view.set_transient_for(self._window)
        self._main_menu: Gtk.Menu = self._builder.get_object('main_menu')
        self._main_infobar: Gtk.InfoBar = self._builder.get_object('main_infobar')
        self._main_infobar.connect('response', lambda b, _: b.set_revealed(False))
        self._main_infobar_label: Gtk.Label = self._builder.get_object('main_infobar_label')
        self._main_infobar.set_revealed(False)
        self._statusbar: Gtk.Statusbar = self._builder.get_object('statusbar')
        self._context = self._statusbar.get_context_id(APP_PACKAGE_NAME)
        self._app_version: Gtk.Label = self._builder.get_object('app_version')
        self._app_version.set_label(f'{APP_NAME} v{APP_VERSION}')
        self._about_dialog: Gtk.AboutDialog = self._builder.get_object('about_dialog')
        self._init_about_dialog()
        self._read_all_button: Gtk.Button = self._builder.get_object("read_all_button")

        # Stress tests
        self._stress_stressor_comboboxtext: Gtk.ComboBoxText = self._builder.get_object('stress_stressor_comboboxtext')
        self._stress_stressor_comboboxtext.connect("changed", self._on_stress_stressor_comboboxtext_changed)
        self._stress_timeout_comboboxtext: Gtk.ComboBoxText = self._builder.get_object('stress_timeout_comboboxtext')
        self._stress_workers_comboboxtext: Gtk.ComboBoxText = self._builder.get_object('stress_workers_comboboxtext')
        self._stress_tests_toggle_button: Gtk.Button = self._builder.get_object("stress_tests_toggle_button")
        self._stress_elapsed_label: Gtk.Label = self._builder.get_object('stress_elapsed_label')
        self._stress_bogo_tot_label: Gtk.Label = self._builder.get_object('stress_bogo_tot_label')
        self._stress_bopsust_label: Gtk.Label = self._builder.get_object('stress_bopsust_label')
        self._stress_elapsed_entry: Gtk.Entry = self._builder.get_object('stress_elapsed_entry')
        self._stress_bogo_tot_entry: Gtk.Entry = self._builder.get_object('stress_bogo_tot_entry')
        self._stress_bopsust_entry: Gtk.Entry = self._builder.get_object('stress_bopsust_entry')
        self._stress_result_image: Gtk.Image = self._builder.get_object('stress_result_image')
        self.update_stress_tests_result(StressTestsResult())

        # Processor
        self._cpu_name_label: Gtk.Label = self._builder.get_object('cpu_name_label')
        self._cpu_specification_label: Gtk.Label = self._builder.get_object('cpu_specification_label')
        self._cpu_family_label: Gtk.Label = self._builder.get_object('cpu_family_label')
        self._cpu_model_label: Gtk.Label = self._builder.get_object('cpu_model_label')
        self._cpu_stepping_label: Gtk.Label = self._builder.get_object('cpu_stepping_label')
        self._cpu_cores_label: Gtk.Label = self._builder.get_object('cpu_cores_label')
        self._cpu_threads_label: Gtk.Label = self._builder.get_object('cpu_threads_label')
        self._cpu_package_label: Gtk.Label = self._builder.get_object('cpu_package_label')
        self._cpu_microcode_label: Gtk.Label = self._builder.get_object('cpu_microcode_label')
        self._cpu_bogomips_label: Gtk.Label = self._builder.get_object('cpu_bogomips_label')
        self._cpu_flags_label: Gtk.Label = self._builder.get_object('cpu_flags_label')
        self._cpu_bugs_label: Gtk.Label = self._builder.get_object('cpu_bugs_label')
        self._cpu_name_entry: Gtk.Entry = self._builder.get_object('cpu_name_entry')
        self._cpu_specification_entry: Gtk.Entry = self._builder.get_object('cpu_specification_entry')
        self._cpu_family_entry: Gtk.Entry = self._builder.get_object('cpu_family_entry')
        self._cpu_model_entry: Gtk.Entry = self._builder.get_object('cpu_model_entry')
        self._cpu_stepping_entry: Gtk.Entry = self._builder.get_object('cpu_stepping_entry')
        self._cpu_cores_entry: Gtk.Entry = self._builder.get_object('cpu_cores_entry')
        self._cpu_threads_entry: Gtk.Entry = self._builder.get_object('cpu_threads_entry')
        self._cpu_package_entry: Gtk.Entry = self._builder.get_object('cpu_package_entry')
        self._cpu_microcode_entry: Gtk.Entry = self._builder.get_object('cpu_microcode_entry')
        self._cpu_bogomips_entry: Gtk.Entry = self._builder.get_object('cpu_bogomips_entry')
        self._cpu_flags_entry: Gtk.Entry = self._builder.get_object('cpu_flags_entry')
        self._cpu_bugs_entry: Gtk.Entry = self._builder.get_object('cpu_bugs_entry')
        self._cpu_flags_dialog: Gtk.Dialog = self._builder.get_object("cpu_flags_dialog")
        self._cpu_flags_dialog.connect("delete-event", hide_on_delete)
        self._cpu_bugs_dialog: Gtk.Dialog = self._builder.get_object("cpu_bugs_dialog")
        self._cpu_bugs_dialog.connect("delete-event", hide_on_delete)
        self._cpu_bugs_tree_view: Gtk.TreeView = self._builder.get_object("cpu_bugs_tree_view")
        self._cpu_bugs_view_all_button: Gtk.Button = self._builder.get_object("cpu_bugs_view_all_button")
        self._cpu_bugs_list_store: Gtk.ListStore = self._builder.get_object("cpu_bugs_list_store")
        self._cpu_physical_package_comboboxtext: Gtk.ComboBoxText = self._builder.get_object(
            'cpu_physical_package_comboboxtext')
        self._cpu_flags_tree_view: Gtk.TreeView = self._builder.get_object("cpu_flags_tree_view")
        self._cpu_flags_view_all_button: Gtk.Button = self._builder.get_object("cpu_flags_view_all_button")
        self._cpu_flags_list_store: Gtk.ListStore = self._builder.get_object("cpu_flags_list_store")

        # Cache
        self._cpu_cache_l1_data_label: Gtk.Label = self._builder.get_object('cpu_cache_l1_data_label')
        self._cpu_cache_l1_inst_label: Gtk.Label = self._builder.get_object('cpu_cache_l1_inst_label')
        self._cpu_cache_l2_label: Gtk.Label = self._builder.get_object('cpu_cache_l2_label')
        self._cpu_cache_l3_label: Gtk.Label = self._builder.get_object('cpu_cache_l3_label')
        self._cpu_cache_l1_data_size_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l1_data_size_entry')
        self._cpu_cache_l1_inst_size_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l1_inst_size_entry')
        self._cpu_cache_l2_size_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l2_size_entry')
        self._cpu_cache_l3_size_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l3_size_entry')
        self._cpu_cache_l1_data_ways_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l1_data_ways_entry')
        self._cpu_cache_l1_inst_ways_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l1_inst_ways_entry')
        self._cpu_cache_l3_ways_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l3_ways_entry')
        self._cpu_cache_l1_data_sets_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l1_data_sets_entry')
        self._cpu_cache_l2_ways_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l2_ways_entry')
        self._cpu_cache_l1_inst_sets_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l1_inst_sets_entry')
        self._cpu_cache_l2_sets_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l2_sets_entry')
        self._cpu_cache_l3_sets_entry: Gtk.Entry = self._builder.get_object('cpu_cache_l3_sets_entry')

        # Motherboard
        self._mobo_board_vendor_label: Gtk.Label = self._builder.get_object('mobo_board_vendor_label')
        self._mobo_board_name_label: Gtk.Label = self._builder.get_object('mobo_board_name_label')
        self._mobo_board_version_label: Gtk.Label = self._builder.get_object('mobo_board_version_label')
        self._mobo_bios_vendor_label: Gtk.Label = self._builder.get_object('mobo_bios_vendor_label')
        self._mobo_bios_version_label: Gtk.Label = self._builder.get_object('mobo_bios_version_label')
        self._mobo_bios_date_label: Gtk.Label = self._builder.get_object('mobo_bios_date_label')
        self._mobo_board_vendor_entry: Gtk.Entry = self._builder.get_object('mobo_board_vendor_entry')
        self._mobo_board_name_entry: Gtk.Entry = self._builder.get_object('mobo_board_name_entry')
        self._mobo_board_version_entry: Gtk.Entry = self._builder.get_object('mobo_board_version_entry')
        self._mobo_bios_vendor_entry: Gtk.Entry = self._builder.get_object('mobo_bios_vendor_entry')
        self._mobo_bios_version_entry: Gtk.Entry = self._builder.get_object('mobo_bios_version_entry')
        self._mobo_bios_date_entry: Gtk.Entry = self._builder.get_object('mobo_bios_date_entry')

        # Memory
        self._mem_type_label: Gtk.Label = self._builder.get_object('mem_type_label')
        self._mem_type_detail_label: Gtk.Label = self._builder.get_object('mem_type_detail_label')
        self._mem_size_label: Gtk.Label = self._builder.get_object('mem_size_label')
        self._mem_speed_label: Gtk.Label = self._builder.get_object('mem_speed_label')
        self._mem_rank_label: Gtk.Label = self._builder.get_object('mem_rank_label')
        self._mem_manufacturer_label: Gtk.Label = self._builder.get_object('mem_manufacturer_label')
        self._mem_part_number_label: Gtk.Label = self._builder.get_object('mem_part_number_label')
        self._mem_bank_comboboxtext: Gtk.ComboBoxText = self._builder.get_object('mem_bank_comboboxtext')
        self._mem_type_entry: Gtk.Entry = self._builder.get_object('mem_type_entry')
        self._mem_type_detail_entry: Gtk.Entry = self._builder.get_object('mem_type_detail_entry')
        self._mem_size_entry: Gtk.Entry = self._builder.get_object('mem_size_entry')
        self._mem_speed_entry: Gtk.Entry = self._builder.get_object('mem_speed_entry')
        self._mem_rank_entry: Gtk.Entry = self._builder.get_object('mem_rank_entry')
        self._mem_manufacturer_entry: Gtk.Entry = self._builder.get_object('mem_manufacturer_entry')
        self._mem_part_number_entry: Gtk.Entry = self._builder.get_object('mem_part_number_entry')
        self._mem_read_all_info_label: Gtk.Label = self._builder.get_object('mem_read_all_info_label')

        # CPU Usage
        self._cpu_core_usage_grid: Gtk.Grid = self._builder.get_object('cpu_core_usage_grid')
        self._cpu_core_usage_cores_levelbars: List[Gtk.LevelBar] = []
        self._cpu_core_usage_cores_labels: List[Gtk.Label] = []
        self._cpu_usage_user_label: Gtk.Label = self._builder.get_object('cpu_usage_user_label')
        self._cpu_usage_nice_label: Gtk.Label = self._builder.get_object('cpu_usage_nice_label')
        self._cpu_usage_system_label: Gtk.Label = self._builder.get_object('cpu_usage_system_label')
        self._cpu_usage_io_wait_label: Gtk.Label = self._builder.get_object('cpu_usage_io_wait_label')
        self._cpu_usage_irq_label: Gtk.Label = self._builder.get_object('cpu_usage_irq_label')
        self._cpu_usage_soft_irq_label: Gtk.Label = self._builder.get_object('cpu_usage_soft_irq_label')
        self._cpu_usage_steal_label: Gtk.Label = self._builder.get_object('cpu_usage_steal_label')
        self._cpu_usage_guest_label: Gtk.Label = self._builder.get_object('cpu_usage_guest_label')
        self._cpu_usage_guest_nice_label: Gtk.Label = self._builder.get_object('cpu_usage_guest_nice_label')
        self._cpu_loadavg_label: Gtk.Label = self._builder.get_object('cpu_loadavg_label')
        self._cpu_usage_user_levelbar: Gtk.LevelBar = self._builder.get_object('cpu_usage_user_levelbar')
        self._cpu_usage_nice_levelbar: Gtk.LevelBar = self._builder.get_object('cpu_usage_nice_levelbar')
        self._cpu_usage_system_levelbar: Gtk.LevelBar = self._builder.get_object('cpu_usage_system_levelbar')
        self._cpu_usage_io_wait_levelbar: Gtk.LevelBar = self._builder.get_object('cpu_usage_io_wait_levelbar')
        self._cpu_usage_irq_levelbar: Gtk.LevelBar = self._builder.get_object('cpu_usage_irq_levelbar')
        self._cpu_usage_soft_irq_levelbar: Gtk.LevelBar = self._builder.get_object('cpu_usage_soft_irq_levelbar')
        self._cpu_usage_steal_levelbar: Gtk.LevelBar = self._builder.get_object('cpu_usage_steal_levelbar')
        self._cpu_usage_guest_levelbar: Gtk.LevelBar = self._builder.get_object('cpu_usage_guest_levelbar')
        self._cpu_usage_guest_nice_levelbar: Gtk.LevelBar = self._builder.get_object('cpu_usage_guest_nice_levelbar')
        self._remove_level_bar_offsets(self._cpu_usage_user_levelbar)
        self._remove_level_bar_offsets(self._cpu_usage_nice_levelbar)
        self._remove_level_bar_offsets(self._cpu_usage_system_levelbar)
        self._remove_level_bar_offsets(self._cpu_usage_io_wait_levelbar)
        self._remove_level_bar_offsets(self._cpu_usage_irq_levelbar)
        self._remove_level_bar_offsets(self._cpu_usage_soft_irq_levelbar)
        self._remove_level_bar_offsets(self._cpu_usage_steal_levelbar)
        self._remove_level_bar_offsets(self._cpu_usage_guest_levelbar)
        self._remove_level_bar_offsets(self._cpu_usage_guest_nice_levelbar)
        self._cpu_loadavg1_entry: Gtk.Entry = self._builder.get_object('cpu_loadavg1_entry')
        self._cpu_loadavg5_entry: Gtk.Entry = self._builder.get_object('cpu_loadavg5_entry')
        self._cpu_loadavg15_entry: Gtk.Entry = self._builder.get_object('cpu_loadavg15_entry')

        # Mem usage
        self._mem_usage_total_label: Gtk.Label = self._builder.get_object('mem_usage_total_label')
        self._mem_usage_total_entry: Gtk.Entry = self._builder.get_object('mem_usage_total_entry')
        self._mem_usage_available_label: Gtk.Label = self._builder.get_object('mem_usage_available_label')
        self._mem_usage_available_entry: Gtk.Entry = self._builder.get_object('mem_usage_available_entry')
        self._mem_usage_levelbar: Gtk.LevelBar = self._builder.get_object('mem_usage_levelbar')
        self._remove_level_bar_offsets(self._mem_usage_levelbar)

        # Clocks
        self._cpu_clocks_tree_store: Gtk.TreeStore = self._builder.get_object('cpu_clocks_tree_store')
        self._cpu_clocks_tree_view: Gtk.TreeView = self._builder.get_object("cpu_clocks_tree_view")
        for column in self._cpu_clocks_tree_view.get_columns():
            column.set_expand(True)

        # Hardware Monitor
        self._hwmon_tree_store: Gtk.TreeStore = self._builder.get_object('hwmon_tree_store')
        self._hwmon_tree_view: Gtk.TreeView = self._builder.get_object("hwmon_tree_view")
        for column in self._hwmon_tree_view.get_columns():
            column.set_expand(True)

    def _init_about_dialog(self) -> None:
        self._about_dialog.set_program_name(APP_NAME)
        self._about_dialog.set_version(APP_VERSION)
        self._about_dialog.set_website(APP_SOURCE_URL)
        self._about_dialog.connect("delete-event", hide_on_delete)
        self._about_dialog.connect("response", hide_on_delete)

    def show(self) -> None:
        self._presenter.on_start()

    def show_main_infobar_message(self, message: str, markup: bool = False) -> None:
        if markup:
            self._main_infobar_label.set_markup(message)
        else:
            self._main_infobar_label.set_label(message)
        self._main_infobar.set_revealed(True)

    def toggle_window_visibility(self) -> None:
        if self._window.props.visible:
            self._window.hide()
        else:
            self._window.show()

    def show_about_dialog(self) -> None:
        self._about_dialog.show()

    def set_statusbar_text(self, text: str) -> None:
        self._statusbar.remove_all(self._context)
        self._statusbar.push(self._context, text)

    def select_physical_package(self, physical_package_id: int) -> None:
        if physical_package_id != self._selected_processor[0]:
            self._selected_processor[0] = physical_package_id
            physical_package = self._system_info.cpu_info.physical_package_id_list[physical_package_id]
            index: int = next(index for index in physical_package if index is not None)
            self._selected_processor[1] = index
            self.init_system_info()

    def select_mem_bank(self, mem_bank_id: int) -> None:
        if mem_bank_id != self._selected_mem_bank:
            self._selected_mem_bank = mem_bank_id
            self._update_memory()

    def open_flags_dialog(self) -> None:
        self._cpu_flags_dialog.show_all()

    def open_bugs_dialog(self) -> None:
        self._cpu_bugs_dialog.show_all()

    def init_system_info(self) -> None:
        _LOG.debug("view init_system_info")
        self._update_cpu_info(self._system_info.cpu_info, init=True)
        self._update_mobo_info()
        self._update_clocks(init=True)
        self._update_cpu_usage()
        self._update_mem_usage()
        self._update_hwmon(init=True)
        self._update_memory()

    def refresh_system_info(self) -> None:
        _LOG.debug('refresh system info')
        self._update_cpu_usage()
        self._update_mem_usage()
        self._update_clocks()
        self._update_hwmon()

    def toggle_stress_tests_button(self, is_running: bool) -> None:
        if is_running:
            self._stress_tests_toggle_button.set_label('Stop')
            self._stress_tests_toggle_button.get_style_context().remove_class("suggested-action")
            self._stress_tests_toggle_button.get_style_context().add_class("destructive-action")

        else:
            self._stress_tests_toggle_button.set_label('Start')
            self._stress_tests_toggle_button.get_style_context().remove_class("destructive-action")
            self._stress_tests_toggle_button.get_style_context().add_class("suggested-action")

    def update_chronometer(self, elapsed: str) -> None:
        self._set_entry_with_label_text('stress_elapsed', elapsed)

    def update_stress_tests_result(self, result: StressTestsResult) -> None:
        if result.successful is not None:
            if result.successful:
                self._stress_result_image.set_visible(True)
                self._stress_result_image.set_from_icon_name(Gtk.STOCK_OK, Gtk.IconSize.SMALL_TOOLBAR)
            else:
                self._stress_result_image.set_from_icon_name(Gtk.STOCK_DIALOG_ERROR, Gtk.IconSize.SMALL_TOOLBAR)
        if result.elapsed is not None:
            elapsed = str(datetime.timedelta(seconds=result.elapsed))
            self._set_entry_with_label_text('stress_elapsed', elapsed[:-3] if elapsed[7] == '.' else elapsed)
        else:
            self._set_entry_with_label_text('stress_elapsed', None)
        self._set_entry_with_label_text('stress_bogo_tot', None if result.bogo_ops is None else str(result.bogo_ops))
        self._set_entry_with_label_text('stress_bopsust', None if result.bopsust is None else f"{result.bopsust:.2f}")
        if result.return_code and result.return_code != 2:
            self.show_error_message_dialog("stress-ng error!", result.error)

    def get_stress_test_config(self) -> Tuple[str, int, int]:
        return (self._stress_stressor_comboboxtext.get_active_id(),
                self._stress_workers_comboboxtext.get_active_id(),
                self._stress_timeout_comboboxtext.get_active_id())

    def _setup_physical_package_combobox(self, cpu_info: CpuInfo) -> None:
        if self._cpu_physical_package_comboboxtext.get_model().iter_n_children() == 0:
            for index in range(len(cpu_info.physical_package_id_list)):
                self._cpu_physical_package_comboboxtext.append(str(index), f"Processor #{index}")
            if self._cpu_physical_package_comboboxtext.get_active() == -1:
                self._cpu_physical_package_comboboxtext.set_active(self._selected_processor[0])
            self._cpu_physical_package_comboboxtext.set_sensitive(
                self._cpu_physical_package_comboboxtext.get_model().iter_n_children() > 1)

    def _setup_flags_widgets(self, flags: Optional[List[str]]) -> None:
        self._set_entry_with_label_text('cpu_flags', filter_flags(flags))
        self._cpu_flags_view_all_button.set_sensitive(flags)
        if flags and self._cpu_flags_tree_view.get_model().iter_n_children() == 0:
            for flag in flags:
                flag_description = CPU_FLAGS.get(flag)
                self._cpu_flags_list_store.append([flag, flag_description])

    def _setup_bugs_widgets(self, bugs: Optional[List[str]]) -> None:
        self._set_entry_with_label_text('cpu_bugs', ', '.join(bugs).replace('_', ' ').title() if bugs else None)
        self._cpu_bugs_view_all_button.set_sensitive(bugs)
        if bugs and self._cpu_bugs_tree_view.get_model().iter_n_children() == 0:
            for bug in bugs:
                bug_description = CPU_BUGS.get(bug)
                self._cpu_bugs_list_store.append([bug, bug_description])

    def _update_cpu_info(self, cpu_info: CpuInfo, init: bool = False) -> None:
        if not cpu_info:
            _LOG.error("CpuInfo is None")
            return

        if init:
            _LOG.debug("view cpu init")

            self._setup_physical_package_combobox(cpu_info)

            processor: Processor = cpu_info.get_processor(self._selected_processor)

            self._set_entry_with_label_text('cpu_bogomips', "%g" % processor.bogomips if processor.bogomips else None)
            text_dict = {
                'size': format_cache_size(processor.cache_l1_data),
                'ways': format_cache_ways(processor.cache_l1_data),
                'sets': format_cache_sets(processor.cache_l1_data)
            }
            self._set_entries_with_label_text('cpu_cache_l1_data', text_dict)
            text_dict = {
                'size': format_cache_size(processor.cache_l1_inst),
                'ways': format_cache_ways(processor.cache_l1_inst),
                'sets': format_cache_sets(processor.cache_l1_inst)
            }
            self._set_entries_with_label_text('cpu_cache_l1_inst', text_dict)
            text_dict = {
                'size': format_cache_size(processor.cache_l2),
                'ways': format_cache_ways(processor.cache_l2),
                'sets': format_cache_sets(processor.cache_l2)
            }
            self._set_entries_with_label_text('cpu_cache_l2', text_dict)
            text_dict = {
                'size': format_cache_size(processor.cache_l3),
                'ways': format_cache_ways(processor.cache_l3),
                'sets': format_cache_sets(processor.cache_l3)
            }
            self._set_entries_with_label_text('cpu_cache_l3', text_dict)
            self._set_entry_with_label_text('cpu_microcode', processor.microcode)
            self._set_entry_with_label_text('cpu_cores', str(processor.cores))
            # self._set_entry_with_label_text('cpu_bus_speed', format_frequency(processor.default_bus_speed), True)
            # multiplier = ("x %g" % processor.default_multiplier) if processor.default_multiplier else None
            # self._set_entry_with_label_text('cpu_multiplier', multiplier, True)
            self._setup_flags_widgets(processor.flags)
            self._setup_bugs_widgets(processor.bugs)
            self._set_entry_with_label_text('cpu_family', format_hex(processor.family))
            self._set_entry_with_label_text('cpu_model', format_hex(processor.model))
            self._set_entry_with_label_text('cpu_stepping', format_hex(processor.stepping))
            # self._set_entry_with_label_text('cpu_lithography', format_length(processor.lithography))
            # self._set_entry_with_label_text('cpu_max_tdp', format_power(processor.max_tdp))
            self._set_entry_with_label_text('cpu_name', processor.name)
            self._set_entry_with_label_text('cpu_package', processor.package)
            self._set_entry_with_label_text('cpu_specification', processor.specification)
            self._set_entry_with_label_text('cpu_threads', str(processor.threads))
            # self._set_label_text('cpu_clock', _('Clocks (Core #%(core_id)d)') % {'core_id': processor.processor_id})
            self._setup_stress_workers_combobox()
        else:
            processor = cpu_info.get_processor(self._selected_processor)
        # self._set_entry_with_label_text('cpu_bus_speed', format_frequency(processor.bus_speed))
        # self._set_entry_with_label_text('cpu_core_speed', format_frequency(processor.core_speed))
        # self._set_entry_with_label_text('cpu_multiplier', "x %g" % processor.multiplier)
        # self._set_entry_with_label_text('cpu_rated_fsb', None)
        # self._set_entry_with_label_text('cpu_v_core', None)

    def _update_mobo_info(self) -> None:
        for attr, value in self._system_info.mobo_info:
            self._set_entry_with_label_text(f"mobo_{attr}", value)

    def _update_cpu_usage(self) -> None:
        if not self._cpu_core_usage_cores_levelbars:
            core_count = len(self._system_info.cpu_usage.cores)
            row_count = math.ceil(core_count / _CORE_USAGE_MAX_PER_ROW)
            self._cpu_core_usage_grid.set_property("height-request", row_count * 64)
            cores_per_row = math.ceil(core_count / row_count)
            for index, value in enumerate(self._system_info.cpu_usage.cores):
                top = (index // cores_per_row) * 2
                levelbar = Gtk.LevelBar(min_value=0,
                                        max_value=100,
                                        value=value,
                                        inverted=True,
                                        mode=Gtk.LevelBarMode.CONTINUOUS)
                self._remove_level_bar_offsets(levelbar)
                levelbar.set_orientation(Gtk.Orientation.VERTICAL)
                levelbar.set_vexpand(True)
                label = Gtk.Label(f"{index + 1}")
                self._cpu_core_usage_cores_labels.insert(index, label)
                self._cpu_core_usage_cores_levelbars.insert(index, levelbar)
                self._cpu_core_usage_grid.attach(levelbar, index % cores_per_row, top, 1, 1)
                self._cpu_core_usage_grid.attach(label, index % cores_per_row, top + 1, 1, 1)
                self._window.show_all()
        else:
            for index, value in enumerate(self._system_info.cpu_usage.cores):
                self._cpu_core_usage_cores_levelbars[index].set_value(value)

        for attr, value in self._system_info.cpu_usage:
            if attr != 'cores':
                self._set_levelbar_with_label_text(f"cpu_usage_{attr}", None if value is None else f"{value}%", value)
        self._update_load_avg(self._cpu_loadavg1_entry,
                              self._system_info.load_avg.load_avg_1,
                              self._system_info.load_avg.get_loadavg_percentage(self._system_info.load_avg.load_avg_1))
        self._update_load_avg(self._cpu_loadavg5_entry,
                              self._system_info.load_avg.load_avg_5,
                              self._system_info.load_avg.get_loadavg_percentage(self._system_info.load_avg.load_avg_5))
        self._update_load_avg(self._cpu_loadavg15_entry,
                              self._system_info.load_avg.load_avg_15,
                              self._system_info.load_avg.get_loadavg_percentage(self._system_info.load_avg.load_avg_15))

    def _update_load_avg(self, load_avg_entry: Gtk.Entry, load_avg: float, percentage: float) -> None:
        self._set_entry_text(load_avg_entry, "{} ({:.1f}%)", load_avg, percentage)
        load_avg_entry.set_progress_fraction(percentage / 100)

    def _update_mem_usage(self) -> None:
        self._set_entry_with_label_text('mem_usage_total', format_size(self._system_info.mem_usage.total))
        self._set_entry_with_label_text('mem_usage_available', format_size(self._system_info.mem_usage.available))
        self._set_levelbar(self._mem_usage_levelbar, self._system_info.mem_usage.percent)

    def _update_clocks(self, init: bool = False) -> None:
        if init:
            self._cpu_clocks_tree_store.clear()
            for physical_package_id, processor in self._system_info.cpu_info.clock_monitored_items.items():
                processor_row = self._cpu_clocks_tree_store.append(None, [physical_package_id,
                                                                          f"Processor {physical_package_id}",
                                                                          "", "", ""])
                for item in processor.values():
                    self._cpu_clocks_tree_store.append(
                        processor_row,
                        [int(item.item_id),
                         item.name,
                         format_frequency(item.value),
                         format_frequency(item.value_min),
                         format_frequency(item.value_max)]
                    )
                self._cpu_clocks_tree_view.expand_all()
        else:
            processor_iter = self._cpu_clocks_tree_store.get_iter_first()
            while processor_iter is not None:
                physical_package = self._cpu_clocks_tree_store[processor_iter][0]
                if self._cpu_clocks_tree_store.iter_has_child(processor_iter):
                    core_iter = self._cpu_clocks_tree_store.iter_children(processor_iter)
                    while core_iter is not None:
                        core_id = self._cpu_clocks_tree_store[core_iter][0]
                        item = self._system_info.cpu_info.get_clock_monitored_item(physical_package, core_id)
                        self._cpu_clocks_tree_store[core_iter][2] = format_frequency(item.value)
                        self._cpu_clocks_tree_store[core_iter][3] = format_frequency(item.value_min)
                        self._cpu_clocks_tree_store[core_iter][4] = format_frequency(item.value_max)
                        core_iter = self._cpu_clocks_tree_store.iter_next(core_iter)
                processor_iter = self._cpu_clocks_tree_store.iter_next(processor_iter)

    def _update_hwmon(self, init: bool = False) -> None:
        if init:
            self._hwmon_tree_store.clear()
            for chip_id, chip in self._system_info.hwmon.hw_monitored_items.items():
                chip_row = self._hwmon_tree_store.append(None, [chip_id, chip_id, "", "", ""])
                for feature_type_id, feature_type in chip.items():
                    feature_type_row = self._hwmon_tree_store.append(
                        chip_row,
                        [str(feature_type_id.value),
                         get_sensors_feature_type_name(feature_type_id),
                         "", "", ""])
                    for item in feature_type.values():
                        self._hwmon_tree_store.append(
                            feature_type_row,
                            [item.item_id,
                             item.name,
                             format_feature_type_value(item.value, item.value_type),
                             format_feature_type_value(item.value_min, item.value_type),
                             format_feature_type_value(item.value_max, item.value_type)]
                        )
            self._hwmon_tree_view.expand_all()
        else:
            chip_iter = self._hwmon_tree_store.get_iter_first()
            while chip_iter is not None:
                chip = self._hwmon_tree_store[chip_iter][0]
                if self._hwmon_tree_store.iter_has_child(chip_iter):
                    feature_type_iter = self._hwmon_tree_store.iter_children(chip_iter)
                    while feature_type_iter is not None:
                        feature_type = self._hwmon_tree_store[feature_type_iter][0]
                        if self._hwmon_tree_store.iter_has_child(feature_type_iter):
                            feature_iter = self._hwmon_tree_store.iter_children(feature_type_iter)
                            while feature_iter is not None:
                                item_id = self._hwmon_tree_store[feature_iter][0]
                                item = self._system_info.hwmon.get_hw_monitored_item(chip,
                                                                                     FeatureType(int(feature_type)),
                                                                                     item_id)
                                self._hwmon_tree_store[feature_iter][2] = format_feature_type_value(item.value,
                                                                                                    item.value_type)
                                self._hwmon_tree_store[feature_iter][3] = format_feature_type_value(item.value_min,
                                                                                                    item.value_type)
                                self._hwmon_tree_store[feature_iter][4] = format_feature_type_value(item.value_max,
                                                                                                    item.value_type)
                                feature_iter = self._hwmon_tree_store.iter_next(feature_iter)
                        feature_type_iter = self._hwmon_tree_store.iter_next(feature_type_iter)
                chip_iter = self._hwmon_tree_store.iter_next(chip_iter)

    def _setup_mem_bank_combobox(self, mem_bank_list: List[MemoryBankInfo]) -> None:
        self._mem_bank_comboboxtext.remove_all()
        for index, mem_bank_info in enumerate(mem_bank_list):
            self._mem_bank_comboboxtext.insert(index, str(index),
                                               f"{mem_bank_info.locator} ({mem_bank_info.bank_locator})")
        if self._mem_bank_comboboxtext.get_active() == -1:
            self._mem_bank_comboboxtext.set_active(self._selected_mem_bank)
        self._mem_bank_comboboxtext.set_sensitive(
            len(mem_bank_list) > 1)

    def _setup_stress_workers_combobox(self) -> None:
        if self._stress_workers_comboboxtext.get_model().iter_n_children() == 0:
            threads = 0
            for physical_package in self._system_info.cpu_info.physical_package_id_list:
                processor: Processor = next(physical_package[index] for index in physical_package if index is not None)
                threads += processor.threads
            self._stress_workers_comboboxtext.remove_all()
            self._stress_workers_comboboxtext.insert(0, str(threads), 'Workers: Auto')
            self._stress_workers_comboboxtext.set_active(0)
            for index in range(1, threads + 1):
                self._stress_workers_comboboxtext.insert(index, str(index), str(index))

    def _on_stress_stressor_comboboxtext_changed(self, combobox: Gtk.ComboBoxText) -> None:
        sensitive = "benchmark" not in combobox.get_active_id()
        self._stress_workers_comboboxtext.set_sensitive(sensitive)
        self._stress_timeout_comboboxtext.set_sensitive(sensitive)

    def _update_memory(self) -> None:
        self._setup_mem_bank_combobox(self._system_info.memory_bank_info_list)
        mem_bank_info = self._system_info.memory_bank_info_list[self._selected_mem_bank]
        self._set_entry_with_label_text('mem_type', mem_bank_info.type)
        self._set_entry_with_label_text('mem_type_detail', mem_bank_info.type_detail)
        self._set_entry_with_label_text('mem_size', mem_bank_info.size)
        self._set_entry_with_label_text('mem_speed', mem_bank_info.speed)
        self._set_entry_with_label_text('mem_rank', mem_bank_info.rank)
        self._set_entry_with_label_text('mem_manufacturer', mem_bank_info.manufacturer)
        self._set_entry_with_label_text('mem_part_number', mem_bank_info.part_number)
        read_all_label_visibility = len(self._system_info.memory_bank_info_list) \
                                    and self._system_info.memory_bank_info_list[0].locator == LOCATOR_DEFAULT_TEXT
        self._mem_read_all_info_label.set_visible(read_all_label_visibility)

    def _set_entry_with_label_text(self,
                                   name: str,
                                   text: Optional[str],
                                   percentage: Optional[float] = None,
                                   disable: bool = False) -> None:
        entry_name = f"_{name}_entry"
        if hasattr(self, entry_name):
            entry: Gtk.Entry = self.__getattribute__(entry_name)
            entry.set_sensitive(text is not None and not disable)
            entry.set_text("" if text is None else text)
            if text is not None:
                entry.set_icon_from_stock(Gtk.EntryIconPosition.PRIMARY, None)
            if percentage is not None:
                entry.set_progress_fraction(percentage / 100)
            label_name = f"_{name}_label"
            label: Gtk.Label = self.__getattribute__(label_name)
            if label is not None:
                label.set_sensitive(text is not None)
            else:
                _LOG.error("label %s not found!", label_name)
        else:
            _LOG.error("entry %s not found!", entry_name)

    def _set_levelbar_with_label_text(self,
                                      name: str,
                                      text: Optional[str],
                                      percentage: Optional[float] = None,
                                      disable: bool = False) -> None:
        levelbar_name = f"_{name}_levelbar"
        if hasattr(self, levelbar_name):
            levelbar: Gtk.LevelBar = self.__getattribute__(levelbar_name)
            levelbar.set_sensitive(text is not None and not disable)
            if text is not None:
                levelbar.set_tooltip_text(text)
            if percentage is not None:
                levelbar.set_value(percentage / 100)
            label_name = f"_{name}_label"
            label: Gtk.Label = self.__getattribute__(label_name)
            if label is not None:
                label.set_sensitive(text is not None)
            else:
                _LOG.error("label %s not found!", label_name)
        else:
            _LOG.error("levelbar %s not found!", levelbar_name)

    def _set_entries_with_label_text(self, base_name: str, text_dict: Dict[str, Optional[str]]) -> None:
        all_none: bool = True
        for postfix, text in text_dict.items():
            entry_name = f"_{base_name}_{postfix}_entry"
            if hasattr(self, entry_name):
                entry: Gtk.Entry = self.__getattribute__(entry_name)
                all_none = False
                entry.set_sensitive(text is not None)
                entry.set_text("" if text is None else text)
        label_name = f"_{base_name}_label"
        if hasattr(self, label_name):
            label: Gtk.Label = self.__getattribute__(label_name)
            label.set_sensitive(not all_none)
        else:
            _LOG.error(f"label {label_name} not found!")

    def _set_label_text(self, name: str, text: Optional[str]) -> None:
        label_name = f"_{name}_label"
        if hasattr(self, label_name):
            label: Gtk.Label = self.__getattribute__(label_name)
            label.set_sensitive(text is not None)
            label.set_text(text if text is not None else '')
        else:
            _LOG.error(f"label {label_name} not found!")

    @staticmethod
    def _set_entry_text(label: Gtk.Entry, text: Optional[str], *args: Any) -> None:
        if text is not None and None not in args:
            label.set_sensitive(True)
            label.set_text(text.format(*args))
        else:
            label.set_sensitive(False)
            label.set_text('')

    @staticmethod
    def _set_label_markup(label: Gtk.Label, markup: Optional[str], *args: Any) -> None:
        if markup is not None and None not in args:
            label.set_sensitive(True)
            label.set_markup(markup.format(*args))
        else:
            label.set_sensitive(False)
            label.set_markup('')

    @staticmethod
    def _remove_level_bar_offsets(levelbar: Gtk.LevelBar) -> None:
        levelbar.remove_offset_value("low")
        levelbar.remove_offset_value("high")
        levelbar.remove_offset_value("full")
        levelbar.remove_offset_value("alert")

    @staticmethod
    def _set_levelbar(levelbar: Gtk.LevelBar, value: Optional[int]) -> None:
        if value is not None:
            levelbar.set_value(value / 100)
            levelbar.set_sensitive(True)
        else:
            levelbar.set_value(0)
            levelbar.set_sensitive(False)

    def show_error_message_dialog(self, title: str, message: str) -> None:
        dialog = Gtk.MessageDialog(self._window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, title)
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
