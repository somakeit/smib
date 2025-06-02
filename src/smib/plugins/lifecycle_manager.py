import logging
import sys
from logging import Logger
from pathlib import Path
from types import ModuleType
from typing import List, Optional, Union

from slack_bolt.app.async_app import AsyncApp

from smib.config import PLUGINS_DIRECTORY
from smib.plugins.plugin import Plugin
from smib.plugins.loaders import PluginLoader, create_default_plugin_loader
from smib.utilities.dynamic_caller import dynamic_caller
from smib.utilities.package import get_actual_module_name


class PluginLifecycleManager:
    def __init__(self, bolt_app: AsyncApp, plugin_loader: Optional[PluginLoader] = None):
        self.bolt_app: AsyncApp = bolt_app
        self.logger: Logger = logging.getLogger(self.__class__.__name__)
        self.plugins_directory: Path = PLUGINS_DIRECTORY.resolve()
        self.plugin_loader: PluginLoader = plugin_loader or create_default_plugin_loader()

        self.plugins: List[Plugin] = []
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

        try:
            plugins = self.plugin_loader.load_all_from_directory(self.plugins_directory)
            valid_plugins = self.validate_plugins(plugins)
            self.register_plugins(valid_plugins)
        except Exception as e:
            self.logger.exception(f"Failed to load plugins: {e}", exc_info=e)

    def register_plugins(self, plugins: List[Plugin]):
        for plugin in plugins:
            try:
                self.preregister_plugin(plugin)
                self.register_plugin(plugin)
                self.postregister_plugin(plugin)

                self.logger.info(f"Registered plugin {plugin.unique_name} ({self.get_relative_path(plugin.path)})")
            except Exception as e:
                self.logger.exception(f"Failed to register plugin {plugin.unique_name} ({self.get_relative_path(plugin.path)}): {e}", exc_info=e)
                self.unregister_plugin(plugin)
                continue

        self.logger.info(f"Registered {len(self.plugins)} plugin(s) ({self.plugin_string})")

    def register_plugin(self, plugin: Plugin):
        try:
            plugin.register(**self.registration_parameters)
        except Exception as e:
            raise
        finally:
            self.plugins.append(plugin)
            self._add_to_map(plugin)

    @staticmethod
    def _get_map_key(plugin: Plugin):
        return {
            'name': plugin.name,
            'unique_name': plugin.unique_name,
            'path': plugin.path,
            'plugin': plugin,
        }

    def _add_to_map(self, plugin: Plugin):
        self.plugin_map.append(self._get_map_key(plugin))

    def _remove_from_map(self, plugin: Plugin):
        self.plugin_map.remove(self._get_map_key(plugin))

    def unregister_plugin(self, plugin: Plugin):
        for unregister_callback in self.plugin_unregister_callbacks:
            unregister_callback(plugin)

        plugin.unregister()
        self.plugins.remove(plugin)
        self._remove_from_map(plugin)

    def preregister_plugin(self, plugin: Plugin):
        for preregister_callback in self.plugin_preregister_callbacks:
            preregister_callback(plugin)

    def postregister_plugin(self, plugin: Plugin):
        for postregister_callback in self.plugin_postregister_callbacks:
            postregister_callback(plugin)

    def validate_plugins(self, plugins: List[Plugin]) -> List[Plugin]:
        valid_plugins: List[Plugin] = []
        for plugin in plugins:
            if self.validate_plugin(plugin):
                valid_plugins.append(plugin)
            else:
                self.logger.info(f'{plugin.unique_name} ({self.get_relative_path(plugin.path)}) is invalid... removing')
                continue

        return valid_plugins

    def validate_plugin(self, plugin: Plugin) -> bool:
        """Validate that a plugin meets the required interface."""
        # All plugins must have metadata with display_name and description
        if not plugin.metadata.display_name or not plugin.metadata.description:
            self.logger.warning(f'{plugin.unique_name} ({plugin.name}) does not have required metadata')
            return False

        # All plugins must have a register method
        if not hasattr(plugin, 'register'):
            self.logger.info(f'{plugin.unique_name} ({plugin.name}) does not have a register method')
            return False

        # Log if recommended metadata is missing
        if not plugin.metadata.author:
            self.logger.info(f'{plugin.unique_name} ({plugin.name}) does not have the recommended author metadata')

        return True

    @property
    def plugin_string(self):
        return ", ".join(plugin.name for plugin in self.plugins) or "None"

    def register_plugin_unregister_callback(self, callback: callable):
        self.plugin_unregister_callbacks.append(callback)

    def register_plugin_preregister_callback(self, callback: callable):
        self.plugin_preregister_callbacks.append(callback)

    def register_plugin_postregister_callback(self, callback: callable):
        self.plugin_postregister_callbacks.append(callback)

    def register_parameter(self, parameter_name: str, parameter: any):
        self.registration_parameters[parameter_name] = parameter

    def get_relative_path(self, plugin_path: Path | str) -> Path:
        """Get the path relative to the plugins directory."""
        path = Path(plugin_path).resolve()
        try:
            return path.relative_to(self.plugins_directory)
        except ValueError:
            # If the path is not relative to the plugins directory, return the path itself
            return path

    def unload_plugins(self):
        self.logger.info(f"Unloading {len(self.plugins)} plugin(s) ({self.plugin_string})")
        for plugin in self.plugins[::]:
            self.unregister_plugin(plugin)
