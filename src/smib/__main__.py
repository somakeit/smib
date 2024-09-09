import asyncio
import base64
import functools
import inspect
import json
import pickle
from asyncio import CancelledError
from enum import StrEnum
from functools import wraps
from http import HTTPStatus
from pathlib import Path
from xml.etree.ElementInclude import include

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

from fastapi.responses import HTMLResponse, FileResponse

from slack_bolt.response import BoltResponse
from smib.bolt_response import CustomBoltResponse

from smib.config import SLACK_APP_TOKEN, SLACK_BOT_TOKEN
from smib.fastapi_handler import AsyncFastAPIEventHandler
from smib.scheduler_handler import AsyncSchedulerEventHandler

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

    @staticmethod
    def __get_slack_args() -> set:
        # Get the Slack AsyncArgs attributes
        return set(AsyncArgs.__annotations__.keys())

    def __get_new_func(self, func: Callable):
        # Retrieve the original signature
        original_sig = Signature.from_callable(func)

        # Get AsyncArgs parameters to be removed
        async_args_params = self.__get_slack_args()

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

                response, response_kwargs = await self.fastapi_handler.handle(req_value, wrapper_kwargs)

                wrapper_kwargs.update(response_kwargs)

                return response

                # return response
            self.app.add_api_route(path, wrapper, *args, methods=methods, **kwargs)
            route = self.app.routes[-1]

            async def matcher(event: dict):
                match_result = route.matches(event['request']['scope'])
                match = Match(match_result[0])
                return match == Match.FULL

            hijacked_func = self._bolt_response_modifier(func)

            self.slack_app.event('http', matchers=[matcher])(hijacked_func)
            return wrapper
        return decorator

    @staticmethod
    def _bolt_response_modifier(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)

            return CustomBoltResponse(status=0, body='', fastapi_response=response, fastapi_kwargs=kwargs)

        return wrapper

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
    async def status(refresh: bool = Query(False)) -> StatusReturn:
        print(f"{refresh=}")
        return StatusReturn(code=123, name=HTTPStatus.IM_A_TEAPOT.name)

    @smib_http.put('/status')
    async def status(http_req: Request, http_resp: Response):
        http_resp.status_code = HTTPStatus.IM_A_TEAPOT
        return {"message": "OK"}

    @smib_http.get('/dashboard', response_class=HTMLResponse, include_in_schema=False)
    async def dashboard() -> str:
        page_content = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Counter</title>
                <style>
                    body {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                        font-family: Arial, sans-serif;
                    }
                    button {
                        padding: 10px 20px;
                        font-size: 16px;
                        margin-top: 10px;
                    }
                </style>
            </head>
            <body>
                <h1 id="counter">0</h1>
                <button onclick="incrementCounter()">Increment</button>
            
                <script>
                    let count = 0;
                    function incrementCounter() {
                        count++;
                        document.getElementById('counter').innerText = count;
                    }
                </script>
            </body>
            </html>
            """

        return page_content

    @smib_http.get('/file/{file_path:path}', response_class=FileResponse)
    async def file(file_path: str):
        path = Path(file_path)
        print(path.absolute())
        return FileResponse(path, media_type="application/octet-stream", filename=path.name)


    scheduler = AsyncIOScheduler()
    job = scheduler.add_job(scheduler_handler.handle, 'interval', minutes=2, name="2_second_schedule_slack")
    job.modify(kwargs={"job_id": job.id,
                       "scheduler": scheduler})

    @slack_app.event("scheduled_job")
    async def handle_scheduled_job(job: Job):
        print(job.name)


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