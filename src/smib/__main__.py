import asyncio
import inspect
from asyncio import CancelledError
from enum import StrEnum
from functools import wraps

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



async def main():
    # logging.basicConfig(level=logging.DEBUG)

    slack_app = AsyncApp(token=SLACK_BOT_TOKEN,
                         request_verification_enabled=False,
                         process_before_response=True,
                         )


    app = FastAPI(debug=True)

    config = Config(app, host='0.0.0.0', port=80, log_level='trace')
    server = Server(config)
    @app.get('/hello')
    async def hello(req: Request):
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

    @slack_app.event("http")
    async def handle_http2(event):
        print(event.get('body', {}).get('scope', {}).get('path', ''))

    socket_mode_handler = AsyncSocketModeHandler(slack_app, app_token=SLACK_APP_TOKEN)
    fastapi_handler = AsyncFastAPIEventHandler(slack_app)
    scheduler_handler = AsyncSchedulerEventHandler(slack_app)

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