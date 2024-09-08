import asyncio
import functools
import inspect
import json
from asyncio import CancelledError
from enum import StrEnum
from functools import wraps
from http import HTTPStatus

from starlette.routing import Match
import makefun
from slack_bolt.kwargs_injection.async_args import AsyncArgs

import logging
from pprint import pprint
from pydantic import BaseModel

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, Query, Body, APIRouter, Response
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_bolt.kwargs_injection.async_utils import AsyncArgs
from fastapi.routing import APIRoute
from uvicorn import Config, Server

from slack_bolt.response import BoltResponse

from smib.config import SLACK_APP_TOKEN, SLACK_BOT_TOKEN
from smib.fastapi_handler import AsyncFastAPIEventHandler
from smib.scheduler_handler import AsyncSchedulerEventHandler


class Method(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

def slack_get(*args, **kwargs):
    pass

def awaitify(sync_func):
    """Wrap a synchronous callable to allow ``await``'ing it"""
    @wraps(sync_func)
    async def async_func(*args, **kwargs):
        return sync_func(*args, **kwargs)
    return async_func

import makefun
from fastapi import FastAPI
from inspect import Signature, Parameter, signature
from typing import Callable, Annotated, Type
from slack_bolt.kwargs_injection.async_args import AsyncArgs

class MessageBody(BaseModel):
    text: str
    who: str
    count: int = 1

class StatusReturn(BaseModel):
    code: int
    name: str
    optional: str | None = None


class SMIBHttp:
    def __init__(self, app: FastAPI, fastapi_handler: AsyncFastAPIEventHandler, slack_app: AsyncApp):
        self.app = app
        self.fastapi_handler = fastapi_handler
        self.slack_app = slack_app

    def __get_slack_args(self) -> set:
        # Get the Slack AsyncArgs attributes
        return set(AsyncArgs.__annotations__.keys())

    def __get_new_func(self, func: Callable):
        # Retrieve the original signature
        original_sig = Signature.from_callable(func)
        pprint(original_sig.return_annotation)

        # Get AsyncArgs parameters to be removed
        async_args_params = self.__get_slack_args()
        print(async_args_params)

        # Create a new list of parameters, excluding those in async_args_params
        new_params = [
            param for param in original_sig.parameters.values()
            if param.name not in async_args_params
        ]

        # Check if a Request parameter is already present, if not, add it
        if not any(param.annotation == Request for param in new_params):
            new_params.insert(0, Parameter('req', Parameter.POSITIONAL_OR_KEYWORD, annotation=Request))

        # Construct a new signature
        new_sig = original_sig.replace(parameters=new_params)
        return makefun.create_function(new_sig, func)

    def __route_decorator(self, path: str, methods: list, *args, **kwargs):
        def decorator(func: Callable):
            custom_func = self.__get_new_func(func)
            pprint(signature(custom_func).return_annotation)

            @makefun.with_signature(signature(custom_func), func_name=func.__name__, doc=func.__doc__)
            async def wrapper(*wrapper_args, **wrapper_kwargs):
                custom_func_sig = signature(custom_func)

                # Extract `req` parameter's name
                req_param_name = next(
                    (param.name for param in custom_func_sig.parameters.values() if param.annotation == Request),
                    None
                )

                req_value = None

                if req_param_name:
                    # Check if `req` is in kwargs
                    if req_param_name in wrapper_kwargs:
                        req_value = wrapper_kwargs[req_param_name]
                    else:
                        # Otherwise, find `req` in args
                        req_value = None
                        for i, (param_name, param) in enumerate(custom_func_sig.parameters.items()):
                            if param_name == req_param_name:
                                req_value = wrapper_args[i]
                                break

                    print(f"Request parameter value: {req_value}")

                print(wrapper_args, wrapper_kwargs)

                # Call the modified handler
                response = await self.fastapi_handler.handle(req_value, wrapper_kwargs)
                if response.body:
                    return json.loads(response.body)
                else:
                    return response

                # return response
            self.app.add_api_route(path, wrapper, *args, methods=methods, **kwargs)
            route = self.app.routes[-1]
            print(type(route))

            async def matcher(event: dict):
                match_result = route.matches(event['request']['scope'])
                match = Match(match_result[0])
                return match == Match.FULL

            #TODO - Utilise fastapi's serialize_response to generate response

            self.slack_app.event('http', matchers=[matcher])(func)
            return wrapper
        return decorator

    def get(self, path: str, *args, **kwargs):
        return self.__route_decorator(path, methods=["GET"], *args, **kwargs)

    def put(self, path: str, *args, **kwargs):
        return self.__route_decorator(path, methods=["PUT"], *args, **kwargs)

async def main():
    # logging.basicConfig(level=logging.DEBUG)

    slack_app = AsyncApp(token=SLACK_BOT_TOKEN,
                         request_verification_enabled=False,
                         process_before_response=True,
                         )

    socket_mode_handler = AsyncSocketModeHandler(slack_app, app_token=SLACK_APP_TOKEN)
    fastapi_handler = AsyncFastAPIEventHandler(slack_app)
    scheduler_handler = AsyncSchedulerEventHandler(slack_app)


    app = FastAPI(debug=True)
    smib_http = SMIBHttp(app, fastapi_handler, slack_app)

    config = Config(app, host='0.0.0.0', port=80)
    server = Server(config)

    @smib_http.get('/status', response_model=StatusReturn)
    async def status(refresh: bool = Query(False)):
        print(f"{refresh=}")
        resp = BoltResponse(body=StatusReturn(code=123, name=HTTPStatus.IM_A_TEAPOT.name).model_dump_json(), status=HTTPStatus.OK)
        return resp
        # return {"123": 123123}

    @smib_http.put('/status')
    async def status(http_req: Request, http_resp: Response):
        http_resp.status_code = HTTPStatus.IM_A_TEAPOT

    @app.get('/hello/{name}')
    async def hello(req: Request, name: str):
        return await fastapi_handler.handle(req)
    @app.get('/state/{method}/{message_}')
    async def hello2(http_request: Request, message_: str, say, method: Method = Method.GET):
        args = inspect.signature(hello2).parameters.keys()
        slack_args = inspect.signature(AsyncArgs.__init__).parameters.keys()

        print(f"{message_=}")
        print(f"{method=}")

        if set(args).intersection(slack_args):
            raise Exception("Slack and HTTP Arg overlap")

        func = http_request.scope['endpoint']
        return await fastapi_handler.handle(http_request)

    @slack_app.event("scheduled_job")
    async def handle_scheduled_job(job: Job):
        print(job.name)

    @slack_app.event("http", matchers = [awaitify(lambda event: event.get('body', {}).get('scope', {}).get('path', '').startswith('/state'))])
    async def handle_http(args, message):
        pprint(message)

    @slack_app.event("http", matchers = [awaitify(lambda event: event.get('body', {}).get('scope', {}).get('path', '').startswith('/hello'))])
    async def handle_http(name, event):
        print(name, event)

    @slack_app.event("http")
    async def handle_http2(event):
        print(event.get('body', {}).get('scope', {}).get('path', ''))

    scheduler = AsyncIOScheduler()
    job = scheduler.add_job(scheduler_handler.handle, 'interval', minutes=2, name="2_second_schedule_slack")
    job.modify(kwargs={"job_id": job.id,
                       "scheduler": scheduler})
    async def scheduler_run():
        scheduler.start()
        print("Scheduler started!")
        await asyncio.sleep(float("inf"))

    socket_task = asyncio.create_task(socket_mode_handler.start_async())
    fastapi_task = asyncio.create_task(server.serve())
    scheduler_task = asyncio.create_task(scheduler_run())

    try:
        await asyncio.gather(socket_task, fastapi_task, scheduler_task)
    except (KeyboardInterrupt, SystemExit, CancelledError):
        await socket_mode_handler.client.close()
        await socket_mode_handler.disconnect_async()
        await server.shutdown()
        return

if __name__ == '__main__':
    asyncio.run(main())