__display_name__ = "Space State"
__description__ = "A plugin to control the space state"
__author__ = "Sam Cork"

from slack_bolt.app.async_app import AsyncApp
from smib.events.interfaces.http_event_interface import HttpEventInterface


def register(slack: AsyncApp, http: HttpEventInterface):
    from .listeners.http import register as register_http_listeners
    from .listeners.slack import register as register_slack_listeners

    register_http_listeners(http)
    register_slack_listeners(slack)
