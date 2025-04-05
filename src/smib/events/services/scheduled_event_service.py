import asyncio
import logging
from logging import Logger

from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from smib.config import SLACK_APP_TOKEN
from smib.utilities.lazy_property import lazy_property

from apscheduler.schedulers.asyncio import AsyncIOScheduler


class ScheduledEventService:
    scheduler: AsyncIOScheduler

    def __init__(self):
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

    @lazy_property
    def scheduler(self) -> AsyncIOScheduler:
        return AsyncIOScheduler()

    async def start(self):
        self.scheduler.start()

    async def stop(self):
        self.scheduler.shutdown()
