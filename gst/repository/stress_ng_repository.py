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
import os
import signal
import subprocess
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Optional, List

import yaml
from injector import singleton, inject

from gst.conf import APP_PACKAGE_NAME
from gst.model.stress_tests_result import StressTestsResult
from gst.repository import PATH_SYS_SYSTEM

_LOG = logging.getLogger(__name__)
PATH_SYS_CPU = PATH_SYS_SYSTEM + "/cpu"


# https://github.com/endlessm/plainbox-provider-checkbox/blob/master/bin/cpu_stress
@singleton
class StressNgRepository:
    @inject
    def __init__(self) -> None:
        self._pid: Optional[int] = None

    def execute(self, stressor_command: str, workers: int, timeout: int, verify: bool) -> StressTestsResult:
        self.terminate()
        result = StressTestsResult()
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            stress_ng_output = Path(tmp_dir_name, APP_PACKAGE_NAME).with_suffix('.yaml')

            cmd: List[str] = [
                'stress-ng',
                '--yaml',
                str(stress_ng_output),
                '--metrics',
                '--times',
                '--no-rand-seed',
                '--temp-path',
                tmp_dir_name,
                '--timeout',
                str(timeout)
            ]

            if verify:
                cmd.append('--verify')

            cmd.extend(stressor_command.format(workers).split())
            _LOG.debug(f"stress-ng command = {cmd}")

            process = subprocess.Popen(cmd,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       stdin=subprocess.PIPE,
                                       preexec_fn=os.setpgrp)
            self._pid = process.pid
            output, error = process.communicate()

            result.return_code = process.returncode
            result.successful = process.returncode == 0
            result.error = error.decode(encoding='UTF-8').strip()
            log_message = f"ret code = {process.returncode};\n" \
                          f"output = {output.decode(encoding='UTF-8').strip()};\n" \
                          f"error = {result.error}"
            if process.returncode == 0:
                _LOG.debug(log_message)
            else:
                _LOG.error(log_message)

            with suppress(OSError), stress_ng_output.open() as stream:
                try:
                    report = yaml.safe_load(stream)
                    _LOG.debug(f"Parsed YAML report: {report}")
                    if report['metrics']:
                        result.elapsed = 0
                        result.bogo_ops = 0
                        result.bopsust = 0
                        for stressor in report['metrics']:
                            result.elapsed += stressor['wall-clock-time']
                            result.bogo_ops += stressor['bogo-ops']
                            result.bopsust += stressor['bogo-ops-per-second-usr-sys-time']
                except yaml.YAMLError as exc:
                    _LOG.exception(exc)

            self._pid = None
        return result

    def is_running(self) -> bool:
        return self._pid is not None

    def terminate(self) -> int:
        if self.is_running():
            os.killpg(os.getpgid(self._pid), signal.SIGTERM)
            self._pid = None
        return 0
