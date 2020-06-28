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
import multiprocessing
import time
from typing import Optional, Any, Tuple

import rx
from gi.repository import GLib
from injector import inject, singleton
from rx import Observable, operators
from rx.disposable import CompositeDisposable
from rx.scheduler import ThreadPoolScheduler
from rx.scheduler.mainloop import GtkScheduler

from gst.conf import APP_NAME, APP_SOURCE_URL, APP_VERSION, APP_ID
from gst.interactor.check_new_version_interactor import CheckNewVersionInteractor
from gst.interactor.get_stressors_interactor import GetStressorsInteractor
from gst.interactor.load_dmi_decode_interactor import LoadDmiDecodeInteractor
from gst.interactor.load_lm_sensors_interactor import LoadLmSensorsInteractor
from gst.interactor.load_proc_cpuinfo_interactor import LoadProcCpuinfoInteractor
from gst.interactor.load_ps_util_interactor import LoadPsUtilInteractor
from gst.interactor.load_sys_devices_cache_interactor import LoadSysDevicesCacheInteractor
from gst.interactor.load_sys_devices_dmi_interactor import LoadSysDevicesDmiInteractor
from gst.interactor.notification_interactor import NotificationInteractor
from gst.interactor.settings_interactor import SettingsInteractor
from gst.interactor.stress_ng_interactor import StressNgInteractor
from gst.model.stress_tests_result import StressTestsResult
from gst.model.system_info import SystemInfo
from gst.presenter.preferences_presenter import PreferencesPresenter
from gst.repository.dmi_decode_repository import DmiDecodeRepositoryResult
from gst.util.view import open_uri, get_default_application

_LOG = logging.getLogger(__name__)
_ADD_NEW_PROFILE_INDEX = -10


class MainViewInterface:
    def init_system_info(self) -> None:
        raise NotImplementedError()

    def refresh_system_info(self) -> None:
        raise NotImplementedError()

    def select_physical_package(self, physical_package_id: int) -> None:
        raise NotImplementedError()

    def select_mem_bank(self, mem_bank_id: int) -> None:
        raise NotImplementedError()

    def open_flags_dialog(self) -> None:
        raise NotImplementedError()

    def open_bugs_dialog(self) -> None:
        raise NotImplementedError()

    def toggle_window_visibility(self) -> None:
        raise NotImplementedError()

    def set_statusbar_text(self, text: str) -> None:
        raise NotImplementedError()

    def show_main_infobar_message(self, message: str, markup: bool = False) -> None:
        raise NotImplementedError()

    def show_about_dialog(self) -> None:
        raise NotImplementedError()

    def toggle_stress_tests_button(self, is_running: bool) -> None:
        raise NotImplementedError()

    def update_chronometer(self, elapsed: str) -> None:
        raise NotImplementedError()

    def update_stress_tests_result(self, result: StressTestsResult) -> None:
        raise NotImplementedError()

    def get_stress_test_config(self) -> Tuple[str, int, int]:
        raise NotImplementedError()

    def show_error_message_dialog(self, title: str, message: str) -> None:
        raise NotImplementedError()


@singleton
class MainPresenter:
    @inject
    def __init__(self,
                 system_info: SystemInfo,
                 preferences_presenter: PreferencesPresenter,
                 load_proc_cpuinfo_interactor: LoadProcCpuinfoInteractor,
                 load_sys_devices_cache_interactor: LoadSysDevicesCacheInteractor,
                 load_sys_devices_dmi_interactor: LoadSysDevicesDmiInteractor,
                 load_lm_sensors_interactor: LoadLmSensorsInteractor,
                 load_dmi_decode_interactor: LoadDmiDecodeInteractor,
                 load_psutil_interactor: LoadPsUtilInteractor,
                 get_stressors_interactor: GetStressorsInteractor,
                 stress_ng_interactor: StressNgInteractor,
                 notify_interactor: NotificationInteractor,
                 settings_interactor: SettingsInteractor,
                 check_new_version_interactor: CheckNewVersionInteractor,
                 composite_disposable: CompositeDisposable,
                 ) -> None:
        _LOG.debug("init MainPresenter ")
        self.main_view: MainViewInterface = MainViewInterface()
        self._system_info: SystemInfo = system_info
        self._preferences_presenter = preferences_presenter
        self._scheduler = ThreadPoolScheduler(multiprocessing.cpu_count())
        self._load_proc_cpuinfo_interactor: LoadProcCpuinfoInteractor = load_proc_cpuinfo_interactor
        self._load_sys_devices_cache_interactor: LoadSysDevicesCacheInteractor = load_sys_devices_cache_interactor
        self._load_sys_devices_dmi_interactor: LoadSysDevicesDmiInteractor = load_sys_devices_dmi_interactor
        self._load_lm_sensors_interactor = load_lm_sensors_interactor
        self._load_dmi_decode_interactor = load_dmi_decode_interactor
        self._load_psutil_interactor = load_psutil_interactor
        self._get_stressors_interactor = get_stressors_interactor
        self._stress_ng_interactor = stress_ng_interactor
        self._notify_interactor = notify_interactor
        self._settings_interactor = settings_interactor
        self._check_new_version_interactor = check_new_version_interactor
        self._composite_disposable: CompositeDisposable = composite_disposable
        self._chronometer_tag: Optional[int] = None
        self._chronometer_start_time: Optional[float] = None
        self._chronometer_stop_time: Optional[float] = None

    def on_start(self) -> None:
        if self._settings_interactor.get_int('settings_check_new_version'):
            self._check_new_version()
        self._composite_disposable.add(rx.just(self._system_info).pipe(
            operators.subscribe_on(self._scheduler),
            operators.flat_map(self._load_psutil),
            operators.flat_map(self._load_proc_cpuinfo),
            operators.flat_map(self._load_sys_devices_cache),
            operators.flat_map(self._load_sys_devices_dmi),
            operators.flat_map(self._load_lm_sensors),
            operators.observe_on(GtkScheduler(GLib)),
        ).subscribe(on_next=lambda _: (self.main_view.init_system_info(), self._start_refresh()),
                    on_error=lambda e: _LOG.exception(f"Refresh error: {str(e)}")))

    def on_menu_settings_clicked(self, *_: Any) -> None:
        self._preferences_presenter.show()

    def on_menu_changelog_clicked(self, *_: Any) -> None:
        open_uri(self._get_changelog_uri())

    def on_menu_about_clicked(self, *_: Any) -> None:
        self.main_view.show_about_dialog()

    @staticmethod
    def on_quit_clicked(*_: Any) -> None:
        get_default_application().quit()

    def on_read_all_button_clicked(self, *_: Any) -> None:
        self._composite_disposable.add(rx.just(self._system_info).pipe(
            operators.subscribe_on(self._scheduler),
            operators.flat_map(self._load_dmi_decode),
            operators.observe_on(GtkScheduler(GLib)),
        ).subscribe(on_next=self._handle_read_all_result,
                    on_error=lambda e: _LOG.exception(f"Refresh error: {str(e)}")))

    def on_stress_tests_toggle_button_clicked(self, *_: Any) -> None:
        if self._stress_ng_interactor.is_running():
            self._composite_disposable.add(self._stress_ng_interactor.terminate().pipe(
                operators.subscribe_on(self._scheduler),
                operators.observe_on(GtkScheduler(GLib)),
                operators.finally_action(self._refresh_stress_tests_toggle_button)
            ).subscribe(on_error=lambda e: _LOG.exception(f"Stop stress test error: {str(e)}")))
        else:
            self._toggle_chronometer(True)
            self.main_view.toggle_stress_tests_button(True)
            stressor_id, workers, timeout = self.main_view.get_stress_test_config()
            stressor_cmd = self._get_stressors_interactor.get(stressor_id)
            verify = True
            if 'benchmark' in stressor_id:
                verify = False
                timeout = 8
                workers = 1 if 'single' in stressor_id else 0

            self._composite_disposable.add(
                self._stress_ng_interactor.execute(stressor_cmd, workers, timeout, verify).pipe(
                    operators.subscribe_on(self._scheduler),
                    operators.observe_on(GtkScheduler(GLib)),
                    operators.finally_action(self._refresh_stress_tests_toggle_button)
                ).subscribe(on_next=self._on_stress_tests_result,
                            on_error=lambda e: _LOG.exception(f"Start stress test error: {str(e)}")))

    def _on_stress_tests_result(self, result: StressTestsResult) -> None:
        self.main_view.update_stress_tests_result(result)
        if result.successful is not None:
            if result.successful:
                self._notify_interactor.show("✔ Successful run completed️")
            else:
                self._notify_interactor.show("❌ Unsuccessful run")

    def _start_refresh(self) -> None:
        _LOG.debug("start refresh")
        refresh_interval = self._settings_interactor.get_int('settings_refresh_interval')
        self._composite_disposable.add(rx.interval(refresh_interval, scheduler=self._scheduler).pipe(
            operators.map(lambda _: self._system_info),
            operators.subscribe_on(self._scheduler),
            operators.flat_map(self._load_proc_cpuinfo),
            operators.flat_map(self._load_lm_sensors),
            operators.flat_map(self._load_psutil),
            operators.observe_on(GtkScheduler(GLib)),
        ).subscribe(on_next=lambda _: self.main_view.refresh_system_info(),
                    on_error=lambda e: _LOG.exception(f"Refresh error: {str(e)}")))

    def on_physical_package_selected(self, widget: Any, *_: Any) -> None:
        index = widget.get_active()
        if index >= 0:
            self.main_view.select_physical_package(index)

    def on_mem_bank_selected(self, widget: Any, *_: Any) -> None:
        index = widget.get_active()
        if index >= 0:
            self.main_view.select_mem_bank(index)

    def on_open_flags_dialog_button_clicked(self, *_: Any) -> None:
        self.main_view.open_flags_dialog()

    def on_open_bugs_dialog_button_clicked(self, *_: Any) -> None:
        self.main_view.open_bugs_dialog()

    def _log_exception_return_system_info_observable(self, ex: Exception, _: Observable) -> Observable:
        _LOG.exception(f"Err = {ex}")
        self.main_view.set_statusbar_text(str(ex))
        observable = rx.just(self._system_info)
        assert isinstance(observable, Observable)
        return observable

    def _execute_stream_interactor(self, system_info: SystemInfo, interactor: Any) -> Observable:
        observable = interactor.execute(system_info).pipe(
            operators.catch(self._log_exception_return_system_info_observable)
        )
        assert isinstance(observable, Observable)
        return observable

    def _load_proc_cpuinfo(self, system_info: SystemInfo) -> Observable:
        return self._execute_stream_interactor(system_info, self._load_proc_cpuinfo_interactor)

    def _load_sys_devices_cache(self, system_info: SystemInfo) -> Observable:
        return self._execute_stream_interactor(system_info, self._load_sys_devices_cache_interactor)

    def _load_sys_devices_dmi(self, system_info: SystemInfo) -> Observable:
        return self._execute_stream_interactor(system_info, self._load_sys_devices_dmi_interactor)

    def _load_lm_sensors(self, system_info: SystemInfo) -> Observable:
        return self._execute_stream_interactor(system_info, self._load_lm_sensors_interactor)

    def _load_dmi_decode(self, system_info: SystemInfo) -> Observable:
        return self._execute_stream_interactor(system_info, self._load_dmi_decode_interactor)

    def _load_psutil(self, system_info: SystemInfo) -> Observable:
        return self._execute_stream_interactor(system_info, self._load_psutil_interactor)

    def _refresh_stress_tests_toggle_button(self) -> None:
        is_running = self._stress_ng_interactor.is_running()
        self._toggle_chronometer(is_running)
        self.main_view.toggle_stress_tests_button(is_running)

    def _toggle_chronometer(self, should_run: bool) -> None:
        if should_run:
            self._chronometer_start_time = time.monotonic()
            self._refresh_chronometer(self._chronometer_start_time)
            self._chronometer_tag = GLib.timeout_add_seconds(1, self._chronometer_tick)
        else:
            if self._chronometer_tag is not None:
                self._chronometer_stop_time = time.monotonic()
                GLib.source_remove(self._chronometer_tag)
                self._chronometer_tag = None

    def _chronometer_tick(self) -> bool:
        self._refresh_chronometer(time.monotonic())
        return True

    def _refresh_chronometer(self, end_time: float) -> None:
        assert self._chronometer_start_time is not None
        elapsed = end_time - self._chronometer_start_time
        self.main_view.update_chronometer(str(datetime.timedelta(seconds=round(elapsed))))

    def _check_new_version(self) -> None:
        self._composite_disposable.add(self._check_new_version_interactor.execute().pipe(
            operators.subscribe_on(self._scheduler),
            operators.observe_on(GtkScheduler(GLib)),
        ).subscribe(on_next=self._handle_new_version_response,
                    on_error=lambda e: _LOG.exception(f"Check new version error: {str(e)}")))

    def _handle_read_all_result(self, result: DmiDecodeRepositoryResult) -> None:
        if result == DmiDecodeRepositoryResult.SUCCESS:
            self.main_view.init_system_info()
            for index, bank_info in enumerate(self._system_info.memory_bank_info_list):
                if bank_info.size and bank_info.size[0].isdigit():
                    self.main_view.select_mem_bank(index)
                    break
            self.main_view.set_statusbar_text("Memory section updated")

        elif result == DmiDecodeRepositoryResult.ERROR_DMI_DECODE_NOT_AVAILABLE:
            self.main_view.show_error_message_dialog(
                "dmidecode not available",
                f"{APP_NAME} uses dmidecode to read the memory information.\n\n"
                "Please make sure that dmidecode is correctly installed and that "
                "the command \"pkexec dmidecode\" runs successfully."
            )
        else:
            self.main_view.show_error_message_dialog(
                "Error while running DmiDecode",
                "Something went wrong while trying to run dmidecode. Check the console output for details."
            )

    def _handle_generic_set_result(self, result: Any, name: str) -> bool:
        if not isinstance(result, bool):
            _LOG.exception(f"Set overclock error: {str(result)}")
            self.main_view.set_statusbar_text(f'Error applying {name}! {str(result)}')
            return False
        if not result:
            self.main_view.set_statusbar_text(f'Error applying {name}!')
            return False
        self.main_view.set_statusbar_text(f'{name.capitalize()} applied')
        return True

    def _handle_new_version_response(self, version: Optional[str]) -> None:
        if version is not None:
            message = f"{APP_NAME} version <b>{version}</b> is available! " \
                      f"Click <a href=\"{self._get_changelog_uri(version)}\"><b>here</b></a> to see what's new."
            self.main_view.show_main_infobar_message(message, True)
            message = f"Version {version} is available! " \
                      f"Click here to see what's new: {self._get_changelog_uri(version)}"
            self._notify_interactor.show("GST update available!", message)

    @staticmethod
    def _get_changelog_uri(version: str = APP_VERSION) -> str:
        return f"{APP_SOURCE_URL}/blob/{version}/CHANGELOG.md"
