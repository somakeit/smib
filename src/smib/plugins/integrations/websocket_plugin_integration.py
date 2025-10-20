import logging
import sys
from logging import Logger
from pathlib import Path

from fastapi import APIRouter

from smib.config import general
from smib.events.interfaces.websocket_event_interface import WebsocketEventInterface
from smib.plugins.plugin import Plugin


class WebsocketPluginIntegration:
    def __init__(self, websocket_event_interface: WebsocketEventInterface):
        self.websocket_event_interface: WebsocketEventInterface = websocket_event_interface

        self.fastapi_app = self.websocket_event_interface.service.fastapi_app
        self.logger: Logger = logging.getLogger(f"{self.__class__.__name__}")

    def disconnect_plugin(self, plugin: Plugin):
        self.logger.info(f"Locating and removing websocket routes in {plugin.unique_name} ({plugin.name})")

        module_path = Path(plugin.module.__file__)
        if module_path.name == "__init__.py":
            module_path = module_path.parent

        for router in [self.fastapi_app,]:
            for route in router.routes[::]:
                if hasattr(route.endpoint, '__module__') and route.endpoint.__module__ in sys.modules:
                    route_module_path = sys.modules[route.endpoint.__module__].__file__
                    if Path(route_module_path).resolve().is_relative_to(module_path):
                        self.logger.debug(f"Removing route {route}")
                        router.routes.remove(route)

    def initialise_plugin_router(self, plugin: Plugin):
        unique_name = plugin.unique_name
        self.websocket_event_interface.current_router = APIRouter(prefix=self.websocket_event_interface.path_prefix, include_in_schema=False)
        self.websocket_event_interface.routers[unique_name] = self.websocket_event_interface.current_router

    def remove_router_if_unused(self, plugin: Plugin):
        router = self.websocket_event_interface.routers.get(plugin.unique_name)
        if len(router.routes) == 0:
            self.logger.debug(f"Removing unused router for {plugin.path.relative_to(general.plugins_directory)}")
            self.websocket_event_interface.routers.pop(plugin.unique_name)


    def finalise_router_setup(self):
        for router in self.websocket_event_interface.routers.values():
            self.fastapi_app.include_router(router)
