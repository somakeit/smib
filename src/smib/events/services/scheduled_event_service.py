import logging
from functools import lru_cache
from logging import Logger
from typing import cast

from apscheduler.schedulers.asyncio import AsyncIOScheduler


class ScheduledEventService:
    def __init__(self) -> None:
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

    @property
    @lru_cache(maxsize=1)
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
