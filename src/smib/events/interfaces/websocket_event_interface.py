import logging
from functools import wraps
from inspect import Signature
from typing import Callable, Any

import makefun
from fastapi import APIRouter
from makefun import remove_signature_parameters
from slack_bolt.app.async_app import AsyncApp
from starlette.routing import BaseRoute
from starlette.websockets import WebSocket

from smib.events import BoltEventType
from smib.events.handlers.websocket_event_handler import WebsocketEventHandler
from smib.events.interfaces import get_reserved_parameter_names, extract_parameter_and_value, \
    find_annotation_in_signature
from smib.events.interfaces.http import generate_route_matcher
from smib.events.services.http_event_service import HttpEventService


class WebsocketEventInterface:
    def __init__(self, bolt_app: AsyncApp, handler: WebsocketEventHandler, service: HttpEventService):
        self.bolt_app = bolt_app
        self.handler = handler
        self.service = service

        self.logger = logging.getLogger(self.__class__.__name__)
        self.path_prefix = '/ws'

        self.routers: dict[str, APIRouter] = {}
        self.current_router: APIRouter = APIRouter(include_in_schema=False)

    def websocket(self, path: str, name: str | None = None, **kwargs):
        def decorator(func: Callable):
            websocket_function_signature: Signature = clean_signature(Signature.from_callable(func))
            if find_annotation_in_signature(WebSocket, websocket_function_signature) is None:
                raise ValueError("Parameter with type WebSocket not found in handler signature")

            @makefun.with_signature(websocket_function_signature,
                                    func_name=func.__name__,
                                    doc=func.__doc__,
                                    module_name=func.__module__
                                    )
            @wraps(func)
            async def wrapper(*wrapper_args: list[Any], **wrapper_kwargs: dict[str, Any]):
                websocket_parameter_value, websocket_parameter_name = extract_websocket_parameter(websocket_function_signature, wrapper_args, wrapper_kwargs)
                self.logger.debug(f"Handling WebSocket connection from {websocket_parameter_value.client} on path {websocket_parameter_value.scope["path"]}")
                await self.handler.handle(websocket_parameter_value, wrapper_kwargs)

            self.current_router.add_api_websocket_route(path, wrapper, name, **kwargs)
            route: BaseRoute = self.current_router.routes[-1]
            self.logger.debug(f"Added WebSocket route: {route.path}")

            matcher: Callable = generate_route_matcher(route)
            self.bolt_app.event(BoltEventType.WEBSOCKET, matchers=[matcher])(func)

            return func
        return decorator


def clean_signature(signature: Signature) -> Signature:
    reserved_parameters: set[str] = get_reserved_parameter_names()
    parameters_to_remove: set[str] = reserved_parameters.intersection(signature.parameters.keys())
    cleaned_signature: Signature = remove_signature_parameters(signature, *parameters_to_remove)
    return cleaned_signature

def extract_websocket_parameter(signature: Signature, args, kwargs) -> tuple[WebSocket, str]:
    return extract_parameter_and_value(WebSocket, signature, args, kwargs)