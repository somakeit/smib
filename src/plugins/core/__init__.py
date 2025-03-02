import httpx
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from smib.events.interfaces.http_event_interface import HttpEventInterface
from fastapi import Response

def register(http: HttpEventInterface, _socket_mode_handler: AsyncSocketModeHandler):
    @http.get("/status")
    async def status(response: Response):
        socket_status = None
        slack_api_status = None
        if _socket_mode_handler.client is not None and _socket_mode_handler.client.is_connected():
            socket_status = "connected"
        else:
            socket_status = "disconnected"

        async with httpx.AsyncClient() as client:
            response = await client.get("https://slack.com/api/api.test")
            if response.status_code == 200:
                slack_api_status = "ok"

        return {
            "socket_status": socket_status,
            "slack_api_status": slack_api_status
        }