import logging
import sys
from logging import Logger
from pathlib import Path
from types import ModuleType

from slack_bolt.app.async_app import AsyncApp

from smib.config import PLUGINS_DIRECTORY
from smib.plugins import import_all_from_directory
from smib.utilities.dynamic_caller import dynamic_caller
from smib.utilities.package import get_actual_module_name


class PluginLifecycleManager:
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app
        self.logger: Logger = logging.getLogger(self.__class__.__name__)
        self.plugins_directory: Path = PLUGINS_DIRECTORY.resolve()

        self.plugins: list[ModuleType] = []
        self.plugin_map: list = []

        self.plugin_unregister_callbacks: list[callable] = []
        self.plugin_preregister_callbacks: list[callable] = []
        self.plugin_postregister_callbacks: list[callable] = []
        self.registration_parameters: dict[str, any] = {}

    def load_plugins(self):
        self.logger.info(f"Resolved plugins directory to {self.plugins_directory}")
        if not self.plugins_directory.exists() or not self.plugins_directory.is_dir():
            self.logger.warning(f"Plugins directory {self.plugins_directory} doesn't exist")
            return

        sys.path.insert(0, str(self.plugins_directory.parent.resolve()))

        modules = import_all_from_directory(self.plugins_directory)
        plugin_modules = self.validate_plugin_modules(modules)
        self.register_plugins(plugin_modules)

    def register_plugins(self, plugin_modules: list[ModuleType]):
        for plugin_module in plugin_modules:
            try:
                self.preregister_plugin(plugin_module)
                self.register_plugin(plugin_module)
                self.postregister_plugin(plugin_module)

                self.logger.info(f"Registered plugin {plugin_module.__name__} ({self.get_relative_path(plugin_module.__file__)})")
            except Exception as e:
                self.logger.exception(f"Failed to register plugin {plugin_module.__name__} ({self.get_relative_path(plugin_module.__file__)}): {e}", exc_info=e)
                self.unregister_plugin(plugin_module)
                continue

        self.logger.info(f"Registered {len(self.plugins)} plugin(s) ({self.plugin_string})")

    def register_plugin(self, plugin_module: ModuleType):
        try:
            dynamic_caller(plugin_module.register, **self.registration_parameters)
        except Exception as e:
            raise
        finally:
            self.plugins.append(plugin_module)
            self._add_to_map(plugin_module)

    @staticmethod
    def _get_map_key(plugin_module: ModuleType):
        return {
            'name': get_actual_module_name(plugin_module),
            'unique_name': plugin_module.__name__,
            'path': Path(plugin_module.__file__),
            'module': plugin_module,
        }

    def _add_to_map(self, plugin_module: ModuleType):
        self.plugin_map.append(self._get_map_key(plugin_module))

    def _remove_from_map(self, plugin_module: ModuleType):
        self.plugin_map.remove(self._get_map_key(plugin_module))

    def unregister_plugin(self, plugin_module: ModuleType):
        for unregister_callback in self.plugin_unregister_callbacks:
            unregister_callback(plugin_module)

        self.plugins.remove(plugin_module)
        self._remove_from_map(plugin_module)

    def preregister_plugin(self, plugin_module: ModuleType):
        for preregister_callback in self.plugin_preregister_callbacks:
            preregister_callback(plugin_module)

    def postregister_plugin(self, plugin_module: ModuleType):
        for postregister_callback in self.plugin_postregister_callbacks:
            postregister_callback(plugin_module)

    def validate_plugin_modules(self, modules: list[ModuleType]) -> list[ModuleType]:
        valid_plugin_modules: list[ModuleType] = []
        for module in modules:
            if self.validate_plugin_module(module):
                valid_plugin_modules.append(module)
            else:
                self.logger.info(f'{module.__name__} ({self.get_relative_path(module.__file__)}) is invalid... removing')
                del sys.modules[module.__name__]
                continue

        return valid_plugin_modules

    def validate_plugin_module(self, module: ModuleType) -> bool:
        valid = True
        if not callable(getattr(module, 'register', None)):
            self.logger.info(f'{module.__name__} ({get_actual_module_name(module)}) does not have a register callable')
            valid = False

        required_attributes = ['__display_name__', '__description__']
        for attribute in required_attributes:
            if not hasattr(module, attribute):
                self.logger.warning(f'{module.__name__} ({get_actual_module_name(module)}) does not have the required {attribute} attribute')
                valid = False

        recommended_attributes = ['__author__']
        for attribute in recommended_attributes:
            if not hasattr(module, attribute):
                self.logger.info(f'{module.__name__} ({get_actual_module_name(module)}) does not have the recommended {attribute} attribute')

        return valid

    @property
    def plugin_string(self):
        return ", ".join(get_actual_module_name(plugin) for plugin in self.plugins) or "None"

    def register_plugin_unregister_callback(self, callback: callable):
        self.plugin_unregister_callbacks.append(callback)

    def register_plugin_preregister_callback(self, callback: callable):
        self.plugin_preregister_callbacks.append(callback)

    def register_plugin_postregister_callback(self, callback: callable):
        self.plugin_postregister_callbacks.append(callback)

    def register_parameter(self, parameter_name: str, parameter: any):
        self.registration_parameters[parameter_name] = parameter

    def get_relative_path(self, plugin_path: Path | str) -> Path:
        return Path(plugin_path).resolve().relative_to(self.plugins_directory)
