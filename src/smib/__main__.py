import asyncio
import inspect
from asyncio import CancelledError
from enum import StrEnum
from functools import wraps
import makefun

import logging
from pprint import pprint

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, Query
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_bolt.kwargs_injection.async_utils import AsyncArgs
from uvicorn import Config, Server

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
from typing import Callable
from slack_bolt.kwargs_injection.async_args import AsyncArgs


class SMIBHttp:
    def __init__(self, app: FastAPI, fastapi_handler):
        self.app = app
        self.fastapi_handler = fastapi_handler  # This would be an instance of your handler

    def __get_async_args_parameters(self):
        # Get the Slack AsyncArgs parameters
        async_args_signature = signature(AsyncArgs)
        return list(async_args_signature.parameters.keys())

    def __modify_signature(self, func, to_remove=None, to_inject=None):
        # Retrieve the original signature
        sig = Signature.from_callable(func)

        # Create a new list of parameters
        params = list(sig.parameters.values())

        # Fetch parameters to remove (from AsyncArgs)
        async_args_params = self.__get_async_args_parameters()
        to_remove = to_remove or []
        to_remove.extend(async_args_params)

        # Remove specified parameters
        params = [param for param in params if param.name not in to_remove]

        # Inject new parameters
        to_inject = to_inject or {}
        for name, param in to_inject.items():
            params.append(Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, default=param))

        # Construct a new signature
        new_sig = sig.replace(parameters=params)
        return new_sig

    def __create_custom_endpoint(self, func: Callable, path: str, methods: list, to_remove=None, to_inject=None):
        new_sig = self.__modify_signature(func, to_remove, to_inject)
        custom_endpoint = makefun.create_function(new_sig, func)

        # Define a wrapper function that includes custom logic
        async def wrapper(req: Request, *args, **kwargs):
            # Custom logic before calling the actual handler
            print(f"Custom logic before handling {path}")

            # Call the fastapi_handler.handle(req) instead of the original handler function
            response = await self.fastapi_handler.handle(req)

            # Custom logic after calling the actual handler
            print("Custom logic after handling")

            return response

        return wrapper

    def __call__(self, path: str, methods: list = None, to_remove=None, to_inject=None, *args, **kwargs):
        if methods is None:
            methods = ["GET"]

        def decorator(func: Callable):
            custom_endpoint = self.__create_custom_endpoint(func, path, methods, to_remove, to_inject)

            for method in methods:
                self.app.add_api_route(path, custom_endpoint, methods=[method], *args, **kwargs)

            return func

        return decorator

    def get(self, path: str, *args, **kwargs):
        return self(path, methods=["GET"], *args, **kwargs)

    def post(self, path: str, *args, **kwargs):
        return self(path, methods=["POST"], *args, **kwargs)

    def put(self, path: str, *args, **kwargs):
        return self(path, methods=["PUT"], *args, **kwargs)

    def patch(self, path: str, *args, **kwargs):
        return self(path, methods=["PATCH"], *args, **kwargs)

    def delete(self, path: str, *args, **kwargs):
        return self(path, methods=["DELETE"], *args, **kwargs)



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
    smib_http = SMIBHttp(app, fastapi_handler)

    config = Config(app, host='0.0.0.0', port=80, log_level='trace')
    server = Server(config)

    @smib_http.get('/hello')
    async def hello(req: Request):
        return await fastapi_handler.handle(req)
    @smib_http.get('/status')
    async def status(req: Request):
        return await fastapi_handler.handle(req)
    @smib_http.get('/event/{event}')
    async def status(req: Request):
        return await fastapi_handler.handle(req)

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