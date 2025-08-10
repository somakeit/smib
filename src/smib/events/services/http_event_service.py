import logging
import socket
from functools import lru_cache
from logging import Logger

from fastapi import FastAPI
from uvicorn import Config, Server

from smib.config import webserver, project, logging as logging_config
from smib.events.middlewares.http_middleware import DeprecatedRouteMiddleware, HttpRequestLoggingMiddleware
from smib.logging_ import get_logging_config


class HttpEventService:
    def __init__(self):
        self.logger: Logger = logging.getLogger(self.__class__.__name__)
        self.openapi_tags: list[dict] = []

    @property
    @lru_cache
    def fastapi_app(self) -> FastAPI:
        root_path = webserver.path_prefix.rstrip('/')
        return FastAPI(
            version=project.version,
            title=project.display_name,
            description=project.description,
            root_path=root_path,
            root_path_in_servers=bool(root_path),
        )

    @property
    @lru_cache
    def uvicorn_config(self) -> Config:
        return Config(self.fastapi_app,
            host=webserver.host,
            port=webserver.port,
            proxy_headers=True,
            forwarded_allow_ips=webserver.forwarded_allow_ips,
            headers=self.headers,
            log_config=get_logging_config(logging_config.log_level),
            access_log=False,
        )

    @property
    @lru_cache
    def uvicorn_server(self) -> Server:
        return Server(config=self.uvicorn_config)

    @property
    @lru_cache
    def headers(self) -> list[tuple[str, str]] | None:
        return [
            ("server", f"{socket.gethostname()}"),
            ("x-app-name", project.name),
            ("x-app-version", project.version),
        ]

    def apply_middlewares(self):
        self.fastapi_app.add_middleware(DeprecatedRouteMiddleware)
        self.fastapi_app.add_middleware(HttpRequestLoggingMiddleware)

    async def start(self):
        # On start, force re-generate swagger docs
        self.fastapi_app.openapi_schema = None
        self.fastapi_app.openapi_tags = self.openapi_tags

        self.apply_middlewares()

        self.fastapi_app.setup()

        self.logger.info(f"Starting webserver with root path prefix '{webserver.path_prefix}'")
        await self.uvicorn_server.serve()

    async def stop(self):
        if self.uvicorn_server.started:
            await self.uvicorn_server.shutdown()
