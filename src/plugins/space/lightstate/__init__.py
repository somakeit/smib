__display_name__ = "Space Light State"
__description__ = "Tracks reported light-derived state for the space"
__author__ = "Sam Cork"

from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface


def register(api: ApiEventInterface):
    from plugins.space.lightstate.listeners.http import register as register_http_listeners

    register_http_listeners(api)