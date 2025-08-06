__display_name__ = "S.M.I.B.H.I.D."
__description__ = "A plugin to contain SMIBHID specific interfaces"
__author__ = "Sam Cork"

from smib.events.interfaces.http_event_interface import HttpEventInterface


def register(http: HttpEventInterface):
    from .ui import register as register_ui_log_handlers
    from .sensor import register as register_sensor_log_handlers

    register_ui_log_handlers(http)
    register_sensor_log_handlers(http)