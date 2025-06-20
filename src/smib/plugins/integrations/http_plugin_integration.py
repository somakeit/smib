import logging
import sys
from logging import Logger
from pathlib import Path
from pprint import pprint
from types import ModuleType
from typing import Optional, cast

from fastapi import APIRouter

from smib.config import PLUGINS_DIRECTORY
from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.plugins.locator import PluginLocator
from smib.plugins.plugin import Plugin, PythonModulePlugin
from smib.utilities.package import get_actual_module_name


class HttpPluginIntegration:
    def __init__(self, http_event_interface: HttpEventInterface):
        self.http_event_interface: HttpEventInterface = http_event_interface

        self.fastapi_app = self.http_event_interface.service.fastapi_app
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

        self.tag_metadata: list[dict] = []


    def disconnect_plugin(self, plugin: Plugin):
        self.logger.info(f"Locating and removing http routes in {plugin.unique_name} ({plugin.name})")
        plugin_path = plugin.path

        module_path = Path(plugin._module.__file__)
        if module_path.name == "__init__.py":
            module_path = module_path.parent

        for router in [self.fastapi_app,]:
            for route in router.routes[::]:
                if hasattr(route.endpoint, '__module__') and route.endpoint.__module__ in sys.modules:
                    route_module_path = sys.modules[route.endpoint.__module__].__file__
                    if Path(route_module_path).resolve().is_relative_to(module_path):
                        self.logger.debug(f"Removing route {route}")
                        router.routes.remove(route)

    @staticmethod
    def get_plugin_tags(plugin: Plugin) -> dict[str, str]:
        return {
            "name": plugin.metadata.display_name,
            "description": plugin.metadata.description,
        }

    def initialise_plugin_router(self, plugin: Plugin):
        unique_name = plugin.unique_name
        tags = self.get_plugin_tags(plugin)
        self.tag_metadata.append(tags)
        self.http_event_interface.current_router = APIRouter(tags=[tags["name"]])
        self.http_event_interface.routers[unique_name] = self.http_event_interface.current_router

    def remove_router_if_unused(self, plugin: Plugin):
        router = self.http_event_interface.routers.get(plugin.unique_name)
        if len(router.routes) == 0:
            self.logger.debug(f"Removing unused router for {plugin.path.relative_to(PLUGINS_DIRECTORY)}")
            self.http_event_interface.routers.pop(plugin.unique_name)
            self.tag_metadata.remove(self.get_plugin_tags(plugin))

    def finalise_http_setup(self):
        self.http_event_interface.service.openapi_tags += self.tag_metadata
        for router in self.http_event_interface.routers.values():
            self.fastapi_app.include_router(router)
