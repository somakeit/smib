__display_name__ = "Space State"
__description__ = "A plugin to control the space state"
__author__ = "Sam Cork"

from slack_bolt.app.async_app import AsyncApp

from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from smib.events.interfaces.websocket_event_interface import WebsocketEventInterface


def register(slack: AsyncApp, api: ApiEventInterface, ws: WebsocketEventInterface):
    from .listeners.http import register as register_http_listeners
    from .listeners.slack import register as register_slack_listeners
    from .listeners.websocket import register as register_websocket_listeners

    register_http_listeners(api)
    register_slack_listeners(slack)
    register_websocket_listeners(ws)
