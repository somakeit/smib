import inspect
from pathlib import Path
from types import ModuleType

from smib.config import PLUGINS_DIRECTORY
from smib.plugins.lifecycle_manager import PluginLifecycleManager
from smib.utilities.package import get_actual_module_name


class PluginLocator:
    def __init__(self, lifecycle_manager: PluginLifecycleManager):
        self.lifecycle_manager = lifecycle_manager

    def get_by_unique_name(self, unique_name: str) -> ModuleType | None:
        plugin = next(filter(lambda p: p["unique_name"] == unique_name, self.lifecycle_manager.plugin_map), None)
        return plugin["module"] if plugin else None

    def get_by_name(self, name: str) -> ModuleType | None:
        plugin = next(filter(lambda p: p["name"] == name, self.lifecycle_manager.plugin_map), None)
        return plugin["module"] if plugin else None

    def get_by_path(self, path: Path) -> ModuleType | None:
        plugin = next(filter(lambda p: p["path"] == path, self.lifecycle_manager.plugin_map), None)
        return plugin["module"] if plugin else None

    @staticmethod
    def get_name(module: ModuleType) -> str:
        return get_actual_module_name(module)

    @staticmethod
    def get_unique_name(module: ModuleType) -> str:
        return module.__name__

    @staticmethod
    def get_path(module: ModuleType) -> Path:
        return Path(module.__file__)

    @staticmethod
    def get_display_name(module: ModuleType) -> str:
        return module.__display_name__

    @staticmethod
    def get_description(module: ModuleType) -> str:
        return module.__description__

    @staticmethod
    def get_author(module: ModuleType) -> str:
        return module.__author__ if hasattr(module, '__author__') else None

    def get_current_plugin(self) -> ModuleType | None:
        """
        Walk up the stack to find the module/package directly under the plugins directory.
        """

        stack = inspect.stack()

        # Walk through the call stack
        for frame_info in stack:
            file_path = inspect.getfile(frame_info[0])

            # Ensure it is a valid file and normalize the path
            resolved_path = Path(file_path).resolve()

            try:

                plugin_module = self.get_by_path(resolved_path)
                if not plugin_module:
                    continue

                return plugin_module

            except ValueError:
                # If the file is not under the plugins directory, continue
                continue

        # If no match is found, return None
        return None

