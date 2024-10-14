from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from smib.config import SLACK_APP_TOKEN


class SlackEventService:
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app = bolt_app
        self.service = AsyncSocketModeHandler(self.bolt_app, app_token=SLACK_APP_TOKEN)

    async def start(self):
        await self.service.start_async()

    async def stop(self):
        await self.service.close_async()
        await self.service.disconnect_async()