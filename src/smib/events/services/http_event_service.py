import logging
import socket
from logging import Logger

from fastapi import FastAPI
from slack_bolt.app.async_app import AsyncApp
from uvicorn import Config, Server

from smib.config import WEBSERVER_HOST, WEBSERVER_PORT, PACKAGE_VERSION, PACKAGE_DISPLAY_NAME, PACKAGE_DESCRIPTION, \
    WEBSERVER_PATH_PREFIX, PACKAGE_NAME, WEBSERVER_FORWARDED_ALLOW_IPS
from smib.utilities.lazy_property import lazy_property
from smib.logging_ import LOGGING_CONFIG

class HttpEventService:
    fastapi_app: FastAPI
    uvicorn_config: Config
    uvicorn_server: Server
    openapi_tags: list[dict]
    headers: list[tuple[str, str]] | None

    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

    @lazy_property
    def openapi_tags(self) -> list[dict]:
        return []

    @lazy_property
    def fastapi_app(self) -> FastAPI:
        return FastAPI(
            version=PACKAGE_VERSION,
            title=PACKAGE_DISPLAY_NAME,
            description=PACKAGE_DESCRIPTION,
            root_path=WEBSERVER_PATH_PREFIX
        )

    @lazy_property
    def uvicorn_config(self) -> Config:
        return Config(self.fastapi_app,
            host=WEBSERVER_HOST,
            port=WEBSERVER_PORT,
            proxy_headers=True,
            forwarded_allow_ips=WEBSERVER_FORWARDED_ALLOW_IPS,
            headers=self.headers,
            log_config=LOGGING_CONFIG
        )

    @lazy_property
    def uvicorn_server(self) -> Server:
        return Server(config=self.uvicorn_config)

    @lazy_property
    def headers(self) -> list[tuple[str, str]] | None:
        return [
            ("server", f"{socket.gethostname()}"),
            ("x-app-name", PACKAGE_NAME),
            ("x-app-version", PACKAGE_VERSION)
        ]

    async def start(self):
        # On start, force re-generate swagger docs
        self.fastapi_app.openapi_schema = None
        self.fastapi_app.openapi_tags = self.openapi_tags
        self.fastapi_app.setup()

        await self.uvicorn_server.serve()

    async def stop(self):
        pass
