import inspect
from pathlib import Path
from types import ModuleType
from typing import Optional

import smib
from smib.config import PLUGINS_DIRECTORY
from smib.plugins.lifecycle_manager import PluginLifecycleManager
from smib.plugins.plugin import Plugin
from smib.utilities.package import get_actual_module_name


class PluginLocator:
    def __init__(self, lifecycle_manager: PluginLifecycleManager):
        self.lifecycle_manager = lifecycle_manager

    def get_by_unique_name(self, unique_name: str) -> Optional[Plugin]:
        plugin_info = next(filter(lambda p: p["unique_name"] == unique_name, self.lifecycle_manager.plugin_map), None)
        return plugin_info["plugin"] if plugin_info else None

    def get_by_name(self, name: str) -> Optional[Plugin]:
        plugin_info = next(filter(lambda p: p["name"] == name, self.lifecycle_manager.plugin_map), None)
        return plugin_info["plugin"] if plugin_info else None

    def get_by_path(self, path: Path) -> Optional[Plugin]:
        plugin_info = next(filter(lambda p: p["path"] == path, self.lifecycle_manager.plugin_map), None)
        return plugin_info["plugin"] if plugin_info else None

    @staticmethod
    def get_name(plugin: Plugin) -> str:
        return plugin.name

    @staticmethod
    def get_unique_name(plugin: Plugin) -> str:
        return plugin.unique_name

    @staticmethod
    def get_path(plugin: Plugin) -> Path:
        return plugin.path

    @staticmethod
    def get_display_name(plugin: Plugin) -> str:
        return plugin.metadata.display_name

    @staticmethod
    def get_description(plugin: Plugin) -> str:
        return plugin.metadata.description

    @staticmethod
    def get_author(plugin: Plugin) -> Optional[str]:
        return plugin.metadata.author

    def get_current_plugin(self) -> Optional[Plugin]:
        """
        Walk up the stack to find the plugin that contains the current code.
        """
        stack = inspect.stack()

        # Walk through the call stack
        for frame_info in stack:
            file_path = inspect.getfile(frame_info[0])

            # Ensure it is a valid file and normalize the path
            resolved_path = Path(file_path).resolve()

            try:
                plugin = self.get_by_path(resolved_path)
                if not plugin:
                    continue

                return plugin

            except ValueError:
                # If the file is not under the plugins directory, continue
                continue

        # If no match is found, return None
        return None
