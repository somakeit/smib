import logging
import sys
from logging import Logger
from pathlib import Path
from pprint import pprint
from types import ModuleType

from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.utilities.package import get_actual_module_name


class HttpPluginIntegration:
    def __init__(self, http_event_interface: HttpEventInterface):
        self.http_event_interface: HttpEventInterface = http_event_interface
        self.fastapi_app = self.http_event_interface.service.fastapi_app
        self.logger: Logger = logging.getLogger(self.__class__.__name__)


    def disconnect_module(self, module: ModuleType):
        self.logger.info(f"Locating http routes in {module.__name__} ({get_actual_module_name(module)})")
        module_path = Path(module.__file__)

        if module_path.name == "__init__.py":
            module_path = module_path.parent


        for route in self.fastapi_app.routes[::]:
            route_module_path = sys.modules[route.endpoint.__module__].__file__
            if Path(route_module_path).resolve().is_relative_to(module_path):
                self.logger.info(f"Removing route {route}")
                self.fastapi_app.routes.remove(route)