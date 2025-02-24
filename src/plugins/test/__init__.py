import inspect

from slack_bolt.app.async_app import AsyncApp

from smib.events.interfaces.http_event_interface import HttpEventInterface


def register(slack: AsyncApp, http: HttpEventInterface):
    pass
