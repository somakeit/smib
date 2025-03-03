import logging
import sys
from pathlib import Path
from types import ModuleType

from slack_bolt.app.async_app import AsyncApp

from smib.utilities.package import get_actual_module_name


class SlackPluginIntegration:
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    def disconnect_plugin(self, plugin: ModuleType):
        self.logger.info(f"Locating slack listeners in {plugin.__name__} ({get_actual_module_name(plugin)})")
        module_path = Path(plugin.__file__)
        if module_path.name == "__init__.py":
            module_path = module_path.parent

        for listener in self.bolt_app._async_listeners[::]:
            listener_path = sys.modules[listener.ack_function.__module__].__file__
            if Path(listener_path).resolve().is_relative_to(module_path):
                self.logger.info(f"Removing listener {listener.ack_function.__name__}")
                self.bolt_app._async_listeners.remove(listener)
