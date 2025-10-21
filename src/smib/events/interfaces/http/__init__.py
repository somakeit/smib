import logging
from functools import wraps
from http import HTTPStatus
from inspect import Signature, Parameter
from typing import Callable, Any

import makefun
from fastapi import Request
from fastapi.routing import APIRouter
from makefun import remove_signature_parameters, add_signature_parameters
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.kwargs_injection.async_args import AsyncArgs
from starlette.responses import JSONResponse, Response
from starlette.routing import Match, BaseRoute

from smib.events import BoltEventType
from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.interfaces import get_reserved_parameter_names, extract_parameter_and_value
from smib.events.requests.copyable_starlette_request import CopyableStarletteRequest
from smib.events.responses.http_bolt_response import HttpBoltResponse
from smib.events.services.http_event_service import HttpEventService


class HttpEventInterface:
    def __init__(self, bolt_app: AsyncApp, handler: HttpEventHandler, service: HttpEventService, path_prefix: str = "", include_in_schema: bool = True, default_response_class: type[Response] = JSONResponse):
        self.bolt_app: AsyncApp = bolt_app
        self.handler: HttpEventHandler = handler
        self.service: HttpEventService = service
        self.path_prefix: str = path_prefix
        self.include_in_schema: bool = include_in_schema
        self.default_response_class: type[Response] = default_response_class

        self.routers: dict[str, APIRouter] = {}

        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_router: APIRouter = APIRouter()

    @property
    def include_router_options(self) -> dict[str, Any]:
        opts = {
            "include_in_schema": self.include_in_schema
        }
        return opts

    @property
    def add_api_route_options(self) -> dict[str, Any]:
        opts = {
            "response_class": self.default_response_class,
            "include_in_schema": self.include_in_schema,
        }
        return opts

    def add_openapi_tag(self, tag: str, description: str):
        self.service.openapi_tags.append({
            "name": tag,
            "description": description,
        })

    def exception_handler(self, exc_class_or_status_code: int | type[Exception]):
        """ See fastapi.FastAPI.exception_handler() for parameters """
        def decorator(func: Callable):
            exception: type[Exception] = exc_class_or_status_code if isinstance(exc_class_or_status_code, type) else None
            status_code: HTTPStatus = HTTPStatus(exc_class_or_status_code) if isinstance(exc_class_or_status_code, int) else None
            if exc_class_or_status_code in self.service.fastapi_app.exception_handlers.keys():
                if exception:
                    self.logger.warning(f"Handler already registered for exception: {exception}. Overriding with new handler.")
                elif status_code:
                    self.logger.warning(f"Handler already registered for status code: {status_code} ({status_code.name}). Overriding with new handler.")
            self.service.fastapi_app.add_exception_handler(exc_class_or_status_code, func)
            return func
        return decorator

    def _route_decorator(self, path: str, methods: list, *args, **kwargs):
        def decorator(*funcs: list[Callable], ack: Callable | None = None, lazy: list[Callable] | None = None):
            if funcs and len(funcs) > 1:
                raise TypeError("Only 1 function may be passed to the decorator")
            if not funcs and ((ack is None and lazy is None) or len(lazy) == 0):
                raise TypeError("No callables provided to the decorator")
            if funcs and (ack or lazy):
                raise TypeError("Default decorator usage cannot be used at same time as Lazy listener")

            func = ack or funcs[0]
            http_function_signature: Signature = clean_signature(Signature.from_callable(func))

            @makefun.with_signature(http_function_signature,
                                    func_name=func.__name__,
                                    doc=func.__doc__,
                                    module_name=func.__module__
                                    )
            @wraps(func)
            async def wrapper(*wrapper_args: list[Any], **wrapper_kwargs: dict[str, Any]):
                request_value, request_parameter_name = extract_request_parameter(http_function_signature, wrapper_args,
                                                                                  wrapper_kwargs)

                # Enforce a copyable request object
                # TODO - This needs proper testing
                request_value = CopyableStarletteRequest(request_value)
                wrapper_kwargs[request_parameter_name] = request_value

                response, response_kwargs = await self.handler.handle(request_value, wrapper_kwargs)
                wrapper_kwargs.update(response_kwargs)
                return response

            self.current_router.add_api_route(path, wrapper, *args, methods=methods, **{**self.add_api_route_options, **kwargs})
            route: BaseRoute = self.current_router.routes[-1]

            matcher: callable = generate_route_matcher(route)
            response_preserving_func = preserve_http_response(func)

            args_: list
            lazy_kwargs: dict
            if ack:
                args_ = []
                lazy_kwargs = {"ack": response_preserving_func, "lazy": lazy}
            else:
                args_ = [response_preserving_func]
                lazy_kwargs = {}
            self.bolt_app.event(BoltEventType.HTTP, matchers=[matcher])(*args_, **lazy_kwargs)
            return func

        return decorator



def preserve_http_response(func: callable) -> callable:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        response = await func(*args, **kwargs)
        return HttpBoltResponse(status=0, body='', fastapi_response=response, fastapi_kwargs=kwargs)
    return wrapper

def generate_route_matcher(route: BaseRoute) -> callable:
    async def matcher(event: dict) -> bool:
        match_result = route.matches(event['request']['scope'])
        match = Match(match_result[0])
        return match == Match.FULL

    return matcher


def extract_request_parameter(signature: Signature, args, kwargs) -> tuple[Request, str]:
    return extract_parameter_and_value(Request, signature, args, kwargs)


def clean_signature(signature: Signature) -> Signature:
    reserved_parameters: set[str] = get_reserved_parameter_names()
    parameters_to_remove: set[str] = reserved_parameters.intersection(signature.parameters.keys())
    cleaned_signature: Signature = remove_signature_parameters(signature, *parameters_to_remove)
    if not any(parameter.annotation == Request for parameter in cleaned_signature.parameters.values()):
        request_parameter: Parameter = Parameter(name='_http_request_', kind=Parameter.POSITIONAL_OR_KEYWORD,
                                                 annotation=Request)
        cleaned_signature = add_signature_parameters(cleaned_signature, first=request_parameter)

    return cleaned_signature

