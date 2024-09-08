from http import HTTPMethod
from pprint import pprint

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from slack_bolt import BoltResponse
from slack_bolt.adapter.starlette.async_handler import to_starlette_response
from slack_bolt.async_app import AsyncApp
from slack_bolt.async_app import AsyncBoltRequest


async def to_async_bolt_request(req: Request) -> AsyncBoltRequest:
    request_body = {
        "type": "event_callback",
        "event": {
            "type": "http",
            "request": {
                "method": HTTPMethod(req.method),
                "scheme": req.url.scheme,
                "url": str(req.url),
                "path": str(req.url.path),
                "query_string": req.url.query,
                "query_params": jsonable_encoder(req.query_params),
            }
        }
    }

    pprint(request_body)

    context = dict(req.path_params)

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