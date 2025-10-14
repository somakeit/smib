__display_name__ = "S.M.I.B.H.I.D."
__description__ = "A plugin to contain SMIBHID specific interfaces"
__author__ = "Sam Cork"

from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface


def register(api: ApiEventInterface, schedule: ScheduledEventInterface):
    from .ui import register as register_ui_log_handlers
    from .sensor import register as register_sensor_log_handlers

    register_ui_log_handlers(api)
    register_sensor_log_handlers(api, schedule)