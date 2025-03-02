import inspect
import json
import sys
from logging import Logger
import logging
from pathlib import Path
from types import ModuleType

from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from smib.config import SLACK_APP_TOKEN
from smib.utilities.lazy_property import lazy_property
from smib.utilities.package import get_actual_module_name


class SlackEventService:
    service: AsyncSocketModeHandler

    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

    @lazy_property
    def service(self) -> AsyncSocketModeHandler:
        service = AsyncSocketModeHandler(self.bolt_app, app_token=SLACK_APP_TOKEN)
        return service

    async def start(self):
        await self.service.start_async()

    async def stop(self):
        await self.service.close_async()

    def disconnect_module(self, module: ModuleType):
        self.logger.info(f"Locating slack listeners in {module.__name__} ({get_actual_module_name(module)})")
        module_path = Path(module.__file__)
        if module_path.name == "__init__.py":
            module_path = module_path.parent

        for listener in self.bolt_app._async_listeners[::]:
            # listener_path = inspect.getfile(inspect.unwrap(listener.ack_function))
            # print(listener_path, listener.ack_function.__module__)
            listener_path = sys.modules[listener.ack_function.__module__].__file__
            if Path(listener_path).resolve().is_relative_to(module_path):
                self.logger.info(f"Removing listener {listener.ack_function.__name__}")
                self.bolt_app._async_listeners.remove(listener)

