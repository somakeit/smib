__display_name__ = "Space State"
__description__ = "A plugin to control the space state"
__author__ = "Sam Cork"

from slack_bolt.app.async_app import AsyncApp

from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface


def register(slack: AsyncApp, api: ApiEventInterface):
    from .listeners.http import register as register_http_listeners
    from .listeners.slack import register as register_slack_listeners

    register_http_listeners(api)
    register_slack_listeners(slack)
