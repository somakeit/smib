from slack_bolt.app.async_app import AsyncApp

from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.services.http_event_service import HttpEventService

class HttpEventInterface:
    def __init__(self, bolt_app: AsyncApp, handler: HttpEventHandler, service: HttpEventService):
        self.bolt_app = bolt_app
        self.handler = handler
        self.service = service

