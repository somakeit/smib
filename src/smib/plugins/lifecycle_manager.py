import logging
import sys
from logging import Logger
from types import ModuleType

from slack_bolt.app.async_app import AsyncApp

from smib.config import PLUGINS_DIRECTORY
from smib.plugins import import_all_from_directory
from smib.utilities.package import get_actual_module_name


class PluginLifecycleManager:
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app
        self.logger: Logger = logging.getLogger(self.__class__.__name__)
        self.plugins_directory = PLUGINS_DIRECTORY.resolve()
        self.unregister_plugin_callbacks: list[callable] = []

    def load_plugins(self):
        self.logger.info(f"Resolved plugins directory to {self.plugins_directory}")
        if not self.plugins_directory.exists() or not self.plugins_directory.is_dir():
            self.logger.warning(f"Plugins directory {self.plugins_directory} doesn't exist")
            return

        modules = import_all_from_directory(self.plugins_directory)
        plugin_modules = self.validate_plugin_modules(modules)
        self.register_plugins(plugin_modules)

    def register_plugins(self, plugin_modules: list[ModuleType]):
        for plugin_module in plugin_modules:
            try:
                plugin_module.register()
                self.logger.info(f"Registered plugin {plugin_module.__name__} ({get_actual_module_name(plugin_module)})")
            except Exception as e:
                self.logger.exception(f"Failed to register plugin {plugin_module.__name__} ({get_actual_module_name(plugin_module)}): {e}", exc_info=e)
                self.unregister_plugin(plugin_module)
                continue

    def unregister_plugin(self, plugin_module: ModuleType):
        for unregister_callback in self.unregister_plugin_callbacks:
            unregister_callback(plugin_module)

    def validate_plugin_modules(self, modules: list[ModuleType]) -> list[ModuleType]:
        valid_plugin_modules: list[ModuleType] = []
        for module in modules:
            if callable(getattr(module, 'register', None)):
                valid_plugin_modules.append(module)
            else:
                self.logger.info(f'{module.__name__} ({get_actual_module_name(module)}) does not have a register callable')
                del sys.modules[module.__name__]
                continue

        return valid_plugin_modules




