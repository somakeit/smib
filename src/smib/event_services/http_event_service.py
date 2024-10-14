from contextlib import asynccontextmanager

from fastapi import FastAPI
from slack_bolt.app.async_app import AsyncApp
from uvicorn import Config, Server
from smib.event_services import EventServiceProtocol


class HttpEventService(EventServiceProtocol):
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app = bolt_app
        self.fastapi_app = FastAPI()
        self.config = Config(self.fastapi_app)
        self.server = Server(config=self.config)

    async def start(self):
        await self.server.serve()

    async def stop(self):
        pass