import asyncio
from typing import Protocol

from slack_bolt.app.async_app import AsyncApp

class EventServiceProtocol(Protocol):
    async def start(self):
        ...

    async def stop(self):
        ...



class EventServiceManager:
    def __init__(self, app: AsyncApp):
        self._services: list[EventServiceProtocol] = []
        self.app = app

    def register(self, service: EventServiceProtocol):
        self._services.append(service)

    async def start_all(self):
        await asyncio.gather(*(service.start() for service in self._services))

    async def stop_all(self):
        await asyncio.gather(*(service.stop() for service in self._services))
