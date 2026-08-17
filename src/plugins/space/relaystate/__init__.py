__display_name__ = "Space Relay State"
__description__ = "Tracks reported relay state and cumulative on-time for the space"
__author__ = "Sam Cork"

from slack_bolt.app.async_app import AsyncApp

from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface


def register(slack: AsyncApp, api: ApiEventInterface):
    from plugins.space.relaystate.listeners.http import register as register_http_listeners

    register_http_listeners(slack, api)
