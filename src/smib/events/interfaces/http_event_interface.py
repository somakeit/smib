from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.services.http_event_service import HttpEventService


class HttpEventInterface:
    def __init__(self, handler: HttpEventHandler, service: HttpEventService):
        self.handler = handler
        self.service = service