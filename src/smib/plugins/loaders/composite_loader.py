"""
Composite plugin loader.

This module provides a composite loader that can handle multiple plugin types.
"""

import logging
from pathlib import Path
from typing import List, Optional

from smib.plugins.plugin import Plugin
from smib.plugins.loaders.plugin_loaders import PluginLoader, PythonModulePluginLoader, PythonPackagePluginLoader


class CompositePluginLoader:
    """Loader that combines multiple loaders to handle different types of plugins."""

    def __init__(self, loaders: List[PluginLoader]):
        self.loaders = loaders

    def load_from_path(self, path: Path, name: Optional[str] = None) -> Plugin:
        """
        Try to load a plugin using each loader until one succeeds.

        Raises ValueError if all loaders fail.
        """
        path = path.resolve()

        if not path.exists():
            raise FileNotFoundError(f"No such file or directory: '{path}'")

        errors = []

        for loader in self.loaders:
            if loader.can_load(path):
                try:
                    return loader.load_from_path(path, name)
                except Exception as e:
                    errors.append(f"{loader.__class__.__name__}: {str(e)}")

        raise ValueError(f"Cannot load plugin from '{path}': no compatible loader found or all loaders failed. Errors: {errors}")

    def load_all_from_directory(self, directory: Path) -> List[Plugin]:
        """Load all plugins from a directory using all loaders."""
        directory = directory.resolve()

        if not directory.is_dir():
            raise NotADirectoryError(f"{directory} is not a directory")

        plugins = []

        for loader in self.loaders:
            try:
                plugins.extend(loader.load_all_from_directory(directory))
            except Exception as e:
                logging.getLogger(__name__).error(f"Error loading plugins with {loader.__class__.__name__}: {e}")

        return plugins

    def can_load(self, path: Path) -> bool:
        """Check if any loader can load the plugin at the given path."""
        return any(loader.can_load(path) for loader in self.loaders)


def create_default_plugin_loader() -> PluginLoader:
    """Create a default plugin loader that can handle all supported plugin types."""
    return CompositePluginLoader([
        PythonModulePluginLoader(),
        PythonPackagePluginLoader(),
    ])
