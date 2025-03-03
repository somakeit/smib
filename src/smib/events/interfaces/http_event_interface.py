import makefun
from fastapi.routing import APIRouter
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.kwargs_injection.async_args import AsyncArgs
from starlette.routing import Match, BaseRoute

from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.responses.http_bolt_response import HttpBoltResponse
from smib.events.services.http_event_service import HttpEventService

from inspect import Signature, Parameter

from makefun import remove_signature_parameters, add_signature_parameters
from functools import wraps
from fastapi import Request

class HttpEventInterface:
    def __init__(self, bolt_app: AsyncApp, handler: HttpEventHandler, service: HttpEventService):
        self.bolt_app: AsyncApp = bolt_app
        self.handler: HttpEventHandler = handler
        self.service: HttpEventService = service
        self.routers: dict[str, APIRouter] = {}

        self.current_router: APIRouter = APIRouter()

    def __route_decorator(self, path: str, methods: list, *args, **kwargs):
        def decorator(func: callable):
            http_function_signature: Signature = clean_signature(Signature.from_callable(func))

            @makefun.with_signature(http_function_signature,
                                    func_name=func.__name__,
                                    doc=func.__doc__,
                                    module_name=func.__module__
                                    )
            @wraps(func)
            async def wrapper(*wrapper_args: list[any], **wrapper_kwargs: dict[str: any]):
                request_value = extract_request_parameter_value(http_function_signature, wrapper_args, wrapper_kwargs)
                response, response_kwargs = await self.handler.handle(request_value, wrapper_kwargs)
                wrapper_kwargs.update(response_kwargs)
                return response

            self.current_router.add_api_route(path, wrapper, *args, methods=methods, **kwargs)
            route: BaseRoute = self.current_router.routes[-1]

            matcher: callable = generate_route_matcher(route)
            response_preserving_func = preserve_http_response(func)

            self.bolt_app.event('http', matchers=[matcher])(response_preserving_func)
            return func

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
        request_parameter: Parameter = Parameter(name='_http_request_', kind=Parameter.POSITIONAL_OR_KEYWORD,
                                                 annotation=Request)
        cleaned_signature = add_signature_parameters(cleaned_signature, first=request_parameter)

    return cleaned_signature


def get_reserved_parameter_names() -> set[str]:
    return set(AsyncArgs.__annotations__.keys())


if __name__ == '__main__':
    async def test_func(say, context, item: str):
        pass


    sig = clean_signature(Signature.from_callable(test_func))
    print(sig.parameters)
