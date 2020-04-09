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

from gi.repository import Gio
from injector import singleton, inject

from gst.conf import APP_ID
from gst.util.view import get_default_application

_LOG = logging.getLogger(__name__)


@singleton
class NotificationInteractor:
    @inject
    def __init__(self) -> None:
        pass

    @staticmethod
    def show(title: str, body: str = "") -> None:
        application = get_default_application()
        notification = Gio.Notification.new(title=title)
        notification.set_body(body)
        iconname = Gio.ThemedIcon.new(iconname=APP_ID)
        notification.set_icon(iconname)
        application.send_notification(None, notification)
