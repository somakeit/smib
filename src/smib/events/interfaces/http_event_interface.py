from typing import Iterator

import makefun
from annotated_types import SupportsGe
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.kwargs_injection.async_args import AsyncArgs
from starlette.routing import Match

from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.services.http_event_service import HttpEventService

from inspect import Signature, Parameter

from makefun import remove_signature_parameters, add_signature_parameters
from functools import wraps
from fastapi import Request


class HttpEventInterface:
    def __init__(self, bolt_app: AsyncApp, handler: HttpEventHandler, service: HttpEventService):
        self.bolt_app = bolt_app
        self.handler = handler
        self.service = service

    def __route_decorator(self, path: str, methods: list, *args, **kwargs):
        @wraps(self.__route_decorator)
        def decorator(func: callable):
            http_function_signature: Signature = clean_signature(Signature.from_callable(func))

            @makefun.with_signature(http_function_signature, func_name=func.__name__, doc=func.__doc__)
            async def wrapper(*wrapper_args: list[any], **wrapper_kwargs: dict[str: any]):
                request_value = extract_request_parameter_value(http_function_signature, wrapper_args, wrapper_kwargs)
                response = await self.handler.handle(request_value, wrapper_kwargs)
                return response

            self.service.fastapi_app.add_api_route(path, wrapper, *args, methods=methods, **kwargs)
            route = self.service.fastapi_app.routes[-1]

            async def matcher(event: dict) -> bool:
                match_result = route.matches(event['request']['scope'])
                match = Match(match_result[0])
                return match == Match.FULL

            self.bolt_app.event('http', matchers=[matcher])(func)
            return wrapper
        return decorator

    def get(self, path: str, *args, **kwargs):
        """ See fastapi.FastAPI.get() for parameters """
        return self.__route_decorator(path, ["GET"], *args, **kwargs)

    def put(self, path: str, *args, **kwargs):
        """ See fastapi.FastAPI.put() for parameters """
        return self.__route_decorator(path, ["PUT"], *args, **kwargs)

    def post(self, path: str, *args, **kwargs):
        """ See fastapi.FastAPI.post() for parameters """
        return self.__route_decorator(path, ["POST"], *args, **kwargs)

    def delete(self, path: str, *args, **kwargs):
        """ See fastapi.FastAPI.delete() for parameters """
        return self.__route_decorator(path, ["DELETE"], *args, **kwargs)

    def patch(self, path: str, *args, **kwargs):
        """ See fastapi.FastAPI.patch() for parameters """
        return self.__route_decorator(path, ["PATCH"], *args, **kwargs)

def extract_request_parameter_value(signature: Signature, args, kwargs) -> Request:
    bound = signature.bind(*args, **kwargs)
    bound.apply_defaults()

    request_parameter = next(
        (param for param in signature.parameters.values() if param.annotation == Request),
        None
    )
    request_value = bound.arguments.get(request_parameter.name) if request_parameter else None
    return request_value

def clean_signature(signature: Signature) -> Signature:
    reserved_parameters: set[str] = get_reserved_parameter_names()
    parameters_to_remove: set[str] = reserved_parameters.intersection(signature.parameters.keys())
    cleaned_signature: Signature = remove_signature_parameters(signature, *parameters_to_remove)
    if not any(parameter.annotation == Request for parameter in cleaned_signature.parameters.values()):
        request_parameter: Parameter = Parameter(name='_http_request_', kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=Request)
        cleaned_signature = add_signature_parameters(cleaned_signature, first=request_parameter)

    return cleaned_signature

def get_reserved_parameter_names() -> set[str]:
    return set(AsyncArgs.__annotations__.keys())

if __name__ == '__main__':
    async def test_func(say, context, item: str):
        pass

    sig = clean_signature(Signature.from_callable(test_func))
    print(sig.parameters)