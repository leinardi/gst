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
import subprocess
from typing import List, Tuple

from gst.util.deployment import is_flatpak

_LOG = logging.getLogger(__name__)
_FLATPAK_COMMAND_PREFIX = ['flatpak-spawn', '--host']


def check_if_command_is_available(command_name: str, check_on_host: bool = False) -> bool:
    cmd = [
        'which',
        command_name
    ]

    # TODO check /usr/sbin/ too
    if check_on_host and is_flatpak():
        cmd = _FLATPAK_COMMAND_PREFIX + cmd

    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               stdin=subprocess.PIPE)
    output, error = process.communicate()

    return_code = process.returncode
    log_message = f"ret code = {process.returncode};\n" \
                  f"output = {output.decode(encoding='UTF-8').strip()};\n" \
                  f"error = {error.decode(encoding='UTF-8').strip()}"
    if process.returncode != 0:
        _LOG.warning(log_message)

    return bool(return_code == 0)


# https://stackoverflow.com/a/4791612/293878
def run_on_host_and_get_stdout(command: List[str], pipe_command: List[str] = None) -> Tuple[int, str, str]:
    if pipe_command is None:
        if is_flatpak():
            command = _FLATPAK_COMMAND_PREFIX + command
        process1 = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        output, error = process1.communicate()
        return process1.returncode, output.decode(encoding='UTF-8').strip(), error.decode(encoding='UTF-8').strip()
    if is_flatpak():
        command = _FLATPAK_COMMAND_PREFIX + command
        pipe_command = _FLATPAK_COMMAND_PREFIX + pipe_command
    process1 = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    process2 = subprocess.Popen(pipe_command, stdin=process1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process1.stdout.close()
    output, error = process1.communicate()
    return process2.returncode, output.decode(encoding='UTF-8').strip(), error.decode(encoding='UTF-8').strip()
