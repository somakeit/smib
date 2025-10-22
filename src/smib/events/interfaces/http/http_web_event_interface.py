from slack_bolt.app.async_app import AsyncApp
from starlette.responses import HTMLResponse

from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.interfaces.http import HttpEventInterface
from smib.events.services.http_event_service import HttpEventService


class WebEventInterface(HttpEventInterface):
    def __init__(self, bolt_app: AsyncApp, handler: HttpEventHandler, service: HttpEventService):
        super().__init__(bolt_app, handler, service, include_in_schema=False, default_response_class=HTMLResponse)

    def get(self, path: str, *args, **kwargs):
        """ See fastapi.FastAPI.get() for parameters """
        return self._route_decorator(path, ["GET"], *args, **kwargs)