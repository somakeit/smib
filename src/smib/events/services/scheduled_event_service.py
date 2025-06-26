import logging
from logging import Logger
from typing import cast

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from smib.utilities.lazy_property import lazy_property


class ScheduledEventService:
    def __init__(self) -> None:
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

    @lazy_property
    def scheduler(self) -> AsyncIOScheduler:
        scheduler = AsyncIOScheduler()
        return scheduler

    async def start(self) -> None:
        # Use cast to help mypy understand the type
        scheduler: AsyncIOScheduler = cast(AsyncIOScheduler, self.scheduler)
        scheduler.start()

    async def stop(self) -> None:
        # Use cast to help mypy understand the type
        scheduler: AsyncIOScheduler = cast(AsyncIOScheduler, self.scheduler)
        if scheduler.running:
            scheduler.remove_all_jobs()
            scheduler.shutdown()
