import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Optional

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.middleware.async_custom_middleware import AsyncCustomMiddleware
from slack_bolt.middleware.async_middleware import AsyncMiddleware

from smib.plugins.plugin import Plugin, PythonModulePlugin
from smib.utilities.package import get_actual_module_name


class SlackPluginIntegration:
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    def disconnect_plugin(self, plugin: Plugin):
        self.disconnect_listeners(plugin)
        self.disconnect_middlewares(plugin)

    def disconnect_listeners(self, plugin: Plugin):
        self.logger.info(f"Locating and removing slack listeners in {plugin.unique_name} ({plugin.name})")

        module_path = Path(plugin._module.__file__)
        if module_path.name == "__init__.py":
            module_path = module_path.parent

        for listener in self.bolt_app._async_listeners[::]:
            if hasattr(listener.ack_function, '__module__') and listener.ack_function.__module__ in sys.modules:
                listener_path = sys.modules[listener.ack_function.__module__].__file__
                if Path(listener_path).resolve().is_relative_to(module_path):
                    self.logger.debug(f"Removing listener {listener.ack_function.__name__}")
                    self.bolt_app._async_listeners.remove(listener)

    def disconnect_middlewares(self, plugin: Plugin):
        self.logger.info(f"Locating and removing slack middleware in {plugin.unique_name} ({plugin.name})")

        module_path = Path(plugin._module.__file__)
        if module_path.name == "__init__.py":
            module_path = module_path.parent

        for middleware in self.bolt_app._async_middleware_list[::]:
            if not isinstance(middleware, AsyncCustomMiddleware):
                continue

            middleware: AsyncCustomMiddleware
            if hasattr(middleware.func, '__module__') and middleware.func.__module__ in sys.modules:
                middleware_path = sys.modules[middleware.func.__module__].__file__
                if Path(middleware_path).resolve().is_relative_to(module_path):
                    self.logger.debug(f"Removing middleware {middleware.func.__name__}")
                    self.bolt_app._async_middleware_list.remove(middleware)
