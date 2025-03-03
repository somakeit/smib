import logging
import sys
from logging import Logger
from pathlib import Path
from pprint import pprint
from types import ModuleType

from fastapi import APIRouter

from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.plugins.locator import PluginLocator
from smib.utilities.package import get_actual_module_name


class HttpPluginIntegration:
    def __init__(self, http_event_interface: HttpEventInterface, plugin_locator: PluginLocator):
        self.http_event_interface: HttpEventInterface = http_event_interface
        self.plugin_locator: PluginLocator = plugin_locator

        self.fastapi_app = self.http_event_interface.service.fastapi_app
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

        self.tag_metadata: list[dict] = []


    def disconnect_plugin(self, plugin: ModuleType):
        self.logger.info(f"Locating http routes in {plugin.__name__} ({get_actual_module_name(plugin)})")
        module_path = Path(plugin.__file__)

        if module_path.name == "__init__.py":
            module_path = module_path.parent

        for route in self.fastapi_app.routes[::]:
            route_module_path = sys.modules[route.endpoint.__module__].__file__
            if Path(route_module_path).resolve().is_relative_to(module_path):
                self.logger.info(f"Removing route {route}")
                self.fastapi_app.routes.remove(route)

    def initialise_plugin_router(self, plugin: ModuleType):
        unique_name = self.plugin_locator.get_unique_name(plugin)
        tag_name = self.plugin_locator.get_display_name(plugin)
        tag_description = self.plugin_locator.get_description(plugin)
        self.tag_metadata.append({
            "name": tag_name,
            "description": tag_description
        })
        self.http_event_interface.current_router = APIRouter(tags=[tag_name])
        self.http_event_interface.routers[unique_name] = self.http_event_interface.current_router

    def finalise_http_setup(self):
        self.http_event_interface.service.openapi_tags += self.tag_metadata
        for router in self.http_event_interface.routers.values():
            self.fastapi_app.include_router(router)
