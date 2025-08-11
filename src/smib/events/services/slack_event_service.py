import json
import logging
from functools import lru_cache
from logging import Logger

from aiohttp import WSMessage
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from smib.config import slack


class SlackEventService:
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

    @property
    @lru_cache(maxsize=1)
    def service(self) -> AsyncSocketModeHandler:
        service = AsyncSocketModeHandler(self.bolt_app, app_token=slack.app_token.get_secret_value(), logger=logging.getLogger("slack_bolt.AsyncSocketModeHandler"))
        service.client.on_message_listeners.append(self.log_number_of_connections)
        return service

    async def log_number_of_connections(self, raw_message: WSMessage):
        json_message = json.loads(raw_message.data)
        if json_message.get("type") == "hello":
            self.logger.info(f"Number of active slack websocket connections: {json_message.get('num_connections')}")

    async def start(self):
        await self.service.start_async()

    async def stop(self):
        await self.service.close_async()

