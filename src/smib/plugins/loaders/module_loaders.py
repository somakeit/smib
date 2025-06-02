"""
Module loaders for Python plugins.

This module provides loaders for Python modules and packages.
This is a backward compatibility layer that wraps the plugin loaders from plugin_loaders.py.
"""

import abc
from pathlib import Path
from types import ModuleType
from typing import List, Optional, Protocol

from smib.plugins.loaders.plugin_loaders import PythonModulePluginLoader, PythonPackagePluginLoader


class PluginLoader(Protocol):
    """Protocol defining the interface for plugin loaders that return ModuleType objects."""

    @abc.abstractmethod
    def load_from_path(self, path: Path, name: Optional[str] = None) -> ModuleType:
        """Load a plugin from a specific path."""
        pass

    @abc.abstractmethod
    def load_all_from_directory(self, directory: Path) -> List[ModuleType]:
        """Load all plugins from a directory."""
        pass


class ModulePluginLoader:
    """Loader for single-file Python modules."""

    def __init__(self):
        self._loader = PythonModulePluginLoader()

    def load_from_path(self, path: Path, name: Optional[str] = None) -> ModuleType:
        """Load a plugin from a .py file."""
        plugin = self._loader.load_from_path(path, name)
        return plugin._module

    def load_all_from_directory(self, directory: Path) -> List[ModuleType]:
        """Load all .py files from a directory as modules."""
        plugins = self._loader.load_all_from_directory(directory)
        return [plugin._module for plugin in plugins]


class PackagePluginLoader:
    """Loader for Python packages (directories with __init__.py)."""

    def __init__(self):
        self._loader = PythonPackagePluginLoader()

    def load_from_path(self, path: Path, name: Optional[str] = None) -> ModuleType:
        """Load a plugin from a directory with an __init__.py file."""
        plugin = self._loader.load_from_path(path, name)
        return plugin._module

    def load_all_from_directory(self, directory: Path) -> List[ModuleType]:
        """Load all directories with __init__.py from a directory as packages."""
        plugins = self._loader.load_all_from_directory(directory)
        return [plugin._module for plugin in plugins]
