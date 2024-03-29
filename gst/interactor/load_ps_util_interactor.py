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

import reactivex
from injector import singleton, inject
from reactivex import Observable

from gst.model.system_info import SystemInfo
from gst.repository.ps_util_repository import PsUtilRepository

_LOG = logging.getLogger(__name__)


@singleton
class LoadPsUtilInteractor:
    @inject
    def __init__(self, psutil_repository: PsUtilRepository) -> None:
        self._psutil_repository = psutil_repository

    def execute(self, system_info: SystemInfo) -> Observable:
        return reactivex.defer(lambda _: reactivex.just(self._psutil_repository.refresh(system_info)))
