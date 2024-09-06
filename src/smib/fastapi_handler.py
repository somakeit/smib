import inspect
from pprint import pprint

from slack_bolt.async_app import AsyncApp
from slack_bolt.async_app import AsyncBoltRequest
from slack_bolt import BoltResponse
from slack_bolt.adapter.starlette.async_handler import to_starlette_response
from slack_bolt.kwargs_injection.async_utils import AsyncArgs
from fastapi import Request, Response

async def to_async_bolt_request(req: Request) -> AsyncBoltRequest:
    request_body = {
        "type": "event_callback",
        "event": {
            "type": "http",
            "body": req.__dict__
        }
    }

    context = {}
    slack_injected_args = inspect.signature(AsyncArgs.__init__).parameters
    for key, value in req.path_params.items():
        context[key] = value


    return AsyncBoltRequest(body=request_body, query=dict(req.query_params), headers=dict(req.headers), mode="fastapi", context=context)

async def to_fastapi_response(response: BoltResponse) -> Response:
    return to_starlette_response(response)



class AsyncFastAPIEventHandler:
    def __init__(self, app: AsyncApp):
        self.app = app

    async def handle(self, req: Request) -> Response:
        bolt_request: AsyncBoltRequest = await to_async_bolt_request(req)
        bolt_response: BoltResponse = await self.app.async_dispatch(bolt_request)
        return await to_fastapi_response(bolt_response)