from slack_bolt.app.async_app import AsyncApp

from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.interfaces.http import HttpEventInterface
from smib.events.services.http_event_service import HttpEventService


class ApiEventInterface(HttpEventInterface):
    def __init__(self, bolt_app: AsyncApp, handler: HttpEventHandler, service: HttpEventService):
        super().__init__(bolt_app, handler, service, path_prefix='/api')

    def get(self, path: str, *args, **kwargs):
        """ See fastapi.FastAPI.get() for parameters """
        return self._route_decorator(path, ["GET"], *args, **kwargs)

    def put(self, path: str, *args, **kwargs):
        """ See fastapi.FastAPI.put() for parameters """
        return self._route_decorator(path, ["PUT"], *args, **kwargs)

    def post(self, path: str, *args, **kwargs):
        """ See fastapi.FastAPI.post() for parameters """
        return self._route_decorator(path, ["POST"], *args, **kwargs)

    def delete(self, path: str, *args, **kwargs):
        """ See fastapi.FastAPI.delete() for parameters """
        return self._route_decorator(path, ["DELETE"], *args, **kwargs)

    def patch(self, path: str, *args, **kwargs):
        """ See fastapi.FastAPI.patch() for parameters """
        return self._route_decorator(path, ["PATCH"], *args, **kwargs)