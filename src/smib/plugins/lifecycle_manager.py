import logging
import sys
from logging import Logger

from slack_bolt.app.async_app import AsyncApp

from smib.config import PLUGINS_DIRECTORY
from smib.plugins import import_all_from_directory, validate_and_register_plugin_modules
from smib.utilities.package import get_actual_module_name


class PluginLifecycleManager:
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app
        self.logger: Logger = logging.getLogger(self.__class__.__name__)
        self.plugins_directory = PLUGINS_DIRECTORY.resolve()

    def load_plugins(self):
        self.logger.info(f"Resolved plugins directory to {self.plugins_directory}")
        if not self.plugins_directory.exists() or not self.plugins_directory.is_dir():
            self.logger.warning(f"Plugins directory {self.plugins_directory} doesnt exist")
            return

        modules = import_all_from_directory(self.plugins_directory)
        for module in modules:
            if not callable(getattr(module, 'register', None)):
                self.logger.info(f"{module.__name__} ({get_actual_module_name(module)}) has no callable named 'register'")
                sys.modules.pop(module.__name__)
                self.logger.info(f"De-imported module {module.__name__} ({get_actual_module_name(module)})")
                continue

            module.register()




