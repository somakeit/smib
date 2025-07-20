import logging
import time
from pprint import pformat

from fastapi import Request, Response
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match

from smib.config import WEBSERVER_LOG_REQUEST_DETAILS
from smib.events.requests.copyable_starlette_request import CopyableStarletteRequest


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


class HttpRequestLoggingMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = {
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/favicon.ico"
    }

    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(self.__class__.__name__)

    def should_log_request(self, request: Request) -> bool:
        all_excluded_paths = self.EXCLUDED_PATHS | {request.scope['root_path'].rstrip('/') + path for path in self.EXCLUDED_PATHS}
        return WEBSERVER_LOG_REQUEST_DETAILS and request.url.path not in all_excluded_paths

    async def dispatch(self, request: Request, call_next) -> Response:
        should_log = self.should_log_request(request)
        
        if should_log:
            self.logger.debug(f"Received {request.method} request to {request.url.path} from {request.client.host}")
            self.logger.debug(f"Request Headers {pformat(request.headers.items())}")
            
            # Safely get request body as JSON
            try:
                req_body = await request.json()
            except Exception:
                req_body = None
            self.logger.debug(f"Request Body {pformat(req_body)}")

        # Measure processing time
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        if should_log:
            self.logger.debug(f"Returning {response.status_code} response to {request.url.path}")
            self.logger.debug(f"Response Headers {pformat(response.headers.items())}")
            self.logger.debug(f"Request processing time: {process_time:.4f} seconds")

            # Capture and reconstruct response body
            res_body = [section async for section in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(res_body))

            try:
                # Attempt to decode the response body
                decoded_body = res_body[0].decode() if res_body else None
                self.logger.debug(f"Response Body: {pformat(decoded_body)}")
            except Exception as e:
                self.logger.debug(f"Could not decode response body: {str(e)}")

        return response
