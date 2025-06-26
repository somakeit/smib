
import logging
from pprint import pprint

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match


class DeprecatedRouteMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        if self.uses_deprecated_route(request):
            self.logger.warning(f"Deprecated endpoint used: {request.method} {request.url.path}; IP: {request.client.host}")
            response.headers.append("Deprecation", "true")

        return response

    @staticmethod
    def uses_deprecated_route(request: Request) -> bool:
        for route in request.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL and getattr(route, "deprecated", False):
                return True
        return False
