import sys
from pathlib import Path
from typing import Type
from xml.dom.minidom import Document

from smib.plugins.lifecycle_manager import PluginLifecycleManager
from smib.plugins.plugin import Plugin, PythonModulePlugin


class DatabasePluginIntegration:
    def __init__(self, plugin_lifecycle_manager: PluginLifecycleManager):
        self.plugin_lifecycle_manager = plugin_lifecycle_manager

    def filter_valid_plugins(self, model: Type[Document]) -> bool:
        model_file = sys.modules[model.__module__].__file__

        for plugin in self.plugin_lifecycle_manager.plugins:

            module_path = Path(plugin._module.__file__)
            if module_path.name == "__init__.py":
                module_path = module_path.parent

            if Path(model_file).resolve().is_relative_to(module_path):
                return True

        return False
