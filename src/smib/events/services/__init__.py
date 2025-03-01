import asyncio
import sys
from logging import Logger
import logging
from types import ModuleType
from typing import Protocol

from collections.abc import Coroutine

class EventServiceProtocol(Protocol):
    async def start(self):
        ...

    async def stop(self):
        ...

    def disconnect_module(self, module: ModuleType):
        ...



class EventServiceManager:
    def __init__(self):
        self._services: list[EventServiceProtocol] = []
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

    def register(self, service: EventServiceProtocol):
        self._services.append(service)

    @property
    def _services_string(self) -> str:
        return ", ".join(service.__class__.__name__ for service in self._services) or "None"

    async def start_all(self):
        if not self._services:
            self.logger.warning("No services registered to start")
            return
        self.logger.info(f"Starting {len(self._services)} service(s) ({self._services_string})")
        services: list[Coroutine[None, None, None]] = [service.start() for service in self._services]
        await asyncio.gather(*services)

    async def stop_all(self):
        if not self._services:
            self.logger.warning("No services registered to stop")
            return
        self.logger.info(f"Stopping {len(self._services)} service(s) ({self._services_string})")
        services: list[Coroutine[None, None, None]] = [service.stop() for service in self._services]
        await asyncio.gather(*services)
