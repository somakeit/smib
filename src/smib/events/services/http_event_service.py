import logging
import sys
from logging import Logger
from pathlib import Path
from types import ModuleType

from fastapi import FastAPI
from fastapi.routing import APIRoute
from slack_bolt.app.async_app import AsyncApp
from uvicorn import Config, Server

from smib.config import WEBSERVER_HOST, WEBSERVER_PORT, PACKAGE_VERSION, PACKAGE_DISPLAY_NAME, PACKAGE_DESCRIPTION
from smib.utilities.lazy_property import lazy_property
from smib.utilities.package import get_actual_module_name


class HttpEventService:
    fastapi_app: FastAPI
    uvicorn_config: Config
    uvicorn_server: Server

    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

    @lazy_property
    def fastapi_app(self) -> FastAPI:
        return FastAPI(
            version=PACKAGE_VERSION,
            title=PACKAGE_DISPLAY_NAME,
            description=PACKAGE_DESCRIPTION
        )

    @lazy_property
    def uvicorn_config(self) -> Config:
        return Config(self.fastapi_app,
            host=WEBSERVER_HOST,
            port=WEBSERVER_PORT,
        )

    @lazy_property
    def uvicorn_server(self) -> Server:
        return Server(config=self.uvicorn_config)

    async def start(self):
        # On start, force re-generate swagger docs
        self.fastapi_app.openapi_schema = None
        self.fastapi_app.setup()

        await self.uvicorn_server.serve()

    async def stop(self):
        pass
