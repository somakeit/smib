import json
from http import HTTPMethod
from pprint import pprint

from fastapi.encoders import jsonable_encoder
from slack_bolt import BoltResponse
from slack_bolt.adapter.starlette.async_handler import to_starlette_response
from slack_bolt.app.async_app import AsyncApp
from fastapi import Request, Response
from slack_bolt.request.async_request import AsyncBoltRequest

from smib.events.handlers import BoltRequestMode, get_slack_signature_headers
from smib.events.responses.http_bolt_response import HttpBoltResponse


class HttpEventHandler:
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app

    async def handle(self, request: Request, context: dict):
        bolt_request: AsyncBoltRequest = await to_async_bolt_request(request, context)
        bolt_response: BoltResponse | HttpBoltResponse = await self.bolt_app.async_dispatch(bolt_request)
        return await to_http_response(bolt_response)

async def to_async_bolt_request(request: Request, context: dict) -> AsyncBoltRequest:
    request_body: dict[str, any] = {
        "type": "event_callback",
        "event": {
            "type": "http",
            "request": {
                "method": HTTPMethod(request.method),
                "scheme": request.url.scheme,
                "url": str(request.url),
                "path": str(request.url.path),
                "query_string": request.url.query,
                "query_params": jsonable_encoder(request.query_params),
                "scope": {
                    "type": request.scope["type"],
                    "method": request.scope["method"],
                    "path": request.scope["path"],
                    "path_params": request.scope["path_params"],
                    "root_path": request.scope["root_path"],
                }
            }
        }
    }

    json_body = json.dumps(request_body)
    headers = dict(request.headers) | get_slack_signature_headers(json_body)

    return AsyncBoltRequest(body=json_body, query=dict(request.query_params), headers=headers, mode=BoltRequestMode.HTTP, context=context)

async def to_http_response(response: BoltResponse) -> tuple[Response, dict]:

    if isinstance(response, HttpBoltResponse):
        return response.fastapi_response, response.fastapi_kwargs

    return to_starlette_response(response), {}