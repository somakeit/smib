import json
import logging

from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from smib.config import SLACK_APP_TOKEN
from smib.utilities.lazy_property import lazy_property


class SlackEventService:
    service: AsyncSocketModeHandler

    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app
        self.logger = logging.getLogger(self.__class__.__name__)

    @lazy_property
    def service(self) -> AsyncSocketModeHandler:
        service = AsyncSocketModeHandler(self.bolt_app, app_token=SLACK_APP_TOKEN)
        return service

    async def start(self):
        await self.service.start_async()

    async def stop(self):
        await self.service.close_async()

