import json
import logging
import time
from functools import lru_cache
from pprint import pformat

from fastapi import Request, Response
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match

from smib.config import webserver


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

    def uses_deprecated_route(self, request: Request) -> bool:
        scope = {
            "type": request.scope["type"],
            "method": request.scope["method"],
            "path": request.scope["path"],
            "path_params": request.scope.get("path_params", {}),
            "root_path": request.scope["root_path"],
        }

        # Convert to string to allow for caching
        scope_str = json.dumps(scope)
        return self._uses_deprecated_route(scope_str)

    @lru_cache(maxsize=128)
    def _uses_deprecated_route(self, scope_str: str) -> bool:
        scope = json.loads(scope_str)
        for route in self.app.routes:
            match, _ = route.matches(scope)
            if match == Match.FULL and getattr(route, "deprecated", False):
                return True
        return False


class HttpRequestLoggingMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = {
        "/openapi.json",
        "/api/docs",
        "/api/docs/oauth2-redirect",
        "/api/redoc",
        "/favicon.ico",
        "/database/docs",
        "/database/openapi.json",
    }

    LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}

    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(self.__class__.__name__)

    def should_log_request(self, request: Request) -> bool:
        all_excluded_paths = self.EXCLUDED_PATHS | {request.scope['root_path'].rstrip('/') + path for path in self.EXCLUDED_PATHS}
        route_loggable: bool = (webserver.log_request_details and request.url.path not in all_excluded_paths
                and not request.url.path.startswith(('/static', request.scope['root_path'].rstrip('/') + '/static')))
        if not route_loggable:
            return False

        if (
            request.client is not None
            and request.client.host in self.LOCAL_HOSTS
            and request.headers.get('x-skip-logging', 'false').lower() == 'true'
        ):
            return False

        return True

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
