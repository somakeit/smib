from fastapi import FastAPI
from slack_bolt.app.async_app import AsyncApp
from uvicorn import Config, Server

from smib.utilities.lazy_property import lazy_property


class HttpEventService:
    fastapi_app: FastAPI
    uvicorn_config: Config
    uvicorn_server: Server

    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app

    @lazy_property
    def fastapi_app(self) -> FastAPI:
        return FastAPI()

    @lazy_property
    def uvicorn_config(self) -> Config:
        return Config(self.fastapi_app)

    @lazy_property
    def uvicorn_server(self) -> Server:
        return Server(config=self.uvicorn_config)

    async def start(self):
        await self.uvicorn_server.serve()

    async def stop(self):
        pass
