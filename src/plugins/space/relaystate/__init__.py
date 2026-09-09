__display_name__ = "Space Relay State"
__description__ = "Tracks reported relay state and cumulative on-time for the space"
__author__ = "Sam Cork"

from slack_bolt.app.async_app import AsyncApp

from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface


def register(slack: AsyncApp, api: ApiEventInterface, schedule: ScheduledEventInterface):
    from plugins.space.relaystate.listeners.http import register as register_http_listeners
    from plugins.space.relaystate.listeners.scheduled import register as register_scheduled_listeners

    register_http_listeners(slack, api)
    register_scheduled_listeners(schedule)
