import asyncio
from asyncio import Task, CancelledError

from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from smib.config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN
from smib.plugins import load_plugins


class SMIB:
    """
    This class implements lazy initialisation of properties.
    This means that properties are only created when first accessed.
    These properties can be set/overridden. This makes it easier to unit test
    """
    def __init__(self):
        self._slack_bolt_app: AsyncApp | None = None
        self._slack_socket_mode_handler: AsyncSocketModeHandler | None = None

    async def start(self):
        load_plugins()
        await self.start_tasks()

    async def start_tasks(self):
        try:
            await asyncio.gather(*self.tasks)
        except (KeyboardInterrupt, SystemExit, CancelledError):
            await self.slack_socket_mode_handler.client.close()
            await self.slack_socket_mode_handler.close_async()


    @property
    def tasks(self) -> list[Task]:
        return [
            asyncio.create_task(self.slack_socket_mode_handler.start_async())
        ]

    @property
    def slack_bolt_app(self) -> AsyncApp:
        if self._slack_bolt_app is None:
            self._slack_bolt_app = AsyncApp(token=SLACK_BOT_TOKEN)
        return self._slack_bolt_app

    @slack_bolt_app.setter
    def slack_bolt_app(self, value):
        self._slack_bolt_app = value

    @property
    def slack_socket_mode_handler(self):
        if self._slack_socket_mode_handler is None:
            self._slack_socket_mode_handler = AsyncSocketModeHandler(self.slack_bolt_app, app_token=SLACK_APP_TOKEN)
        return self._slack_socket_mode_handler

    @slack_bolt_app.setter
    def slack_bolt_app(self, value):
        self._slack_socket_mode_handler = value

