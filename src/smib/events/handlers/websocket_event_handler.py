import json
from typing import Any

from slack_bolt import BoltResponse
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.request.async_request import AsyncBoltRequest
from starlette.websockets import WebSocket

from smib.events import BoltEventType
from smib.events.handlers import get_slack_signature_headers, BoltRequestMode


class WebsocketEventHandler:
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app = bolt_app

    async def handle(self, websocket: WebSocket, context: dict):
        bolt_request: AsyncBoltRequest = await to_async_bolt_request(websocket, context)
        _: BoltResponse = await self.bolt_app.async_dispatch(bolt_request)

async def to_async_bolt_request(websocket: WebSocket, context: dict) -> AsyncBoltRequest:
    request_body: dict[str, Any] = {
        "type": "event_callback",
        "event": {
            "type": BoltEventType.WEBSOCKET,
            "request": {
                "scope": {
                    "type": websocket.scope["type"],
                    "path": websocket.scope["path"],
                    "path_params": websocket.scope["path_params"],
                    "root_path": websocket.scope["root_path"],
                }
            }
        }
    }

    json_body = json.dumps(request_body)
    headers = dict(websocket.headers) | get_slack_signature_headers(json_body)
    return AsyncBoltRequest(body=json_body, query=dict(websocket.query_params), headers=headers, mode=BoltRequestMode.WEBSOCKET, context=context)

