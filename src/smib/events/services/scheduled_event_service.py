import logging
from logging import Logger

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from smib.utilities.lazy_property import lazy_property


class ScheduledEventService:
    scheduler: AsyncIOScheduler

    def __init__(self):
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

    @lazy_property
    def scheduler(self) -> AsyncIOScheduler:
        scheduler = AsyncIOScheduler()
        return scheduler

    async def start(self):
        self.scheduler.start()

    async def stop(self):
        self.scheduler.remove_all_jobs()
        self.scheduler.shutdown()
