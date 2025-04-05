import logging
from logging import Logger

from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from smib.config import SLACK_APP_TOKEN
from smib.utilities.lazy_property import lazy_property


class ScheduledEventService:

    def __init__(self):
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

    async def start(self):
        ...

    async def stop(self):
        ...
