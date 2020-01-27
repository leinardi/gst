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

from injector import singleton, inject

_LOG = logging.getLogger(__name__)


@singleton
class GetStressorsInteractor:
    _benchmark_timeout = '8'
    _stressors_dict = {
        'cpu-all': '--cpu {0} --cpu-method all',
        'cpu-ackermann': '--cpu {0} --cpu-method ackermann',
        'cpu-factorial': '--cpu {0} --cpu-method factorial',
        'cpu-gamma': '--cpu {0} --cpu-method gamma',
        'cpu-int128decimal64': '--cpu {0} --cpu-method int128decimal64',
        'matrix-all': '--matrix {0} --matrix-method all',
        'matrix-prod': '--matrix {0} --matrix-size 375 --matrix-method prod',
        'bsearch': '--bsearch {0} --bsearch-size 1000000',
        'lsearch': '--lsearch {0} --lsearch-size 4950',
        'qsort': '--qsort {0} --qsort-size 126000',
        'benchmark': '--cpu {0} --cpu-method ackermann '
                     '--matrix {0} --matrix-size 375 --matrix-method prod '
                     '--bsearch {0} --bsearch-size 1000000 '
                     '--lsearch {0} --lsearch-size 4950 '
                     '--qsort {0} --qsort-size 126000 '
                     '--sequential 0 ',
        'benchmark-single-core': '--cpu {0} --cpu-method ackermann '
                                 '--matrix {0} --matrix-size 375 --matrix-method prod '
                                 '--bsearch {0} --bsearch-size 1000000 '
                                 '--lsearch {0} --lsearch-size 4950 '
                                 '--qsort {0} --qsort-size 126000 '
                                 '--sequential 0 '
    }

    @inject
    def __init__(self) -> None:
        pass

    def get(self, stressor_id: str) -> str:
        return self._stressors_dict[stressor_id]
