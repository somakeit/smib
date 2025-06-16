"""
Plugin loaders for Python plugins.

This module provides loaders for Python modules and packages that return Plugin objects.
"""

import abc
import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import List, Optional, Protocol

from smib.plugins.plugin import Plugin, PythonModulePlugin


class PluginLoader(Protocol):
    """Protocol defining the interface for plugin loaders that return Plugin objects."""

    @abc.abstractmethod
    def load_from_path(self, path: Path, name: Optional[str] = None) -> Plugin:
        """Load a plugin from a specific path."""
        pass

    @abc.abstractmethod
    def load_all_from_directory(self, directory: Path) -> List[Plugin]:
        """Load all plugins from a directory."""
        pass

    @abc.abstractmethod
    def can_load(self, path: Path) -> bool:
        """Check if this loader can load the plugin at the given path."""
        pass


class PythonModulePluginLoader:
    """Loader for Python module plugins."""

    def load_from_path(self, path: Path, name: Optional[str] = None) -> Plugin:
        """Load a plugin from a .py file."""
        path = path.resolve()
        module_name = name or path.with_suffix('').name

        # Ensure the module is a .py file
        if not path.suffix == ".py":
            raise ImportError(f"Module is not a python (.py) file {path}")

        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None:
            raise ImportError(f"Failed to create module spec for {path}")

        module = importlib.util.module_from_spec(spec)

        if module_name in sys.modules:
            raise ImportError(f"Module {module_name} already exists")

        sys.modules[module_name] = module

        if spec.loader is None:
            raise ImportError(f"Module loader is None for {path}")

        spec.loader.exec_module(module)

        return PythonModulePlugin(module, path)

    def load_all_from_directory(self, directory: Path) -> List[Plugin]:
        """Load all .py files from a directory as plugins."""
        logger = logging.getLogger(__name__)
        directory = directory.resolve()

        if not directory.is_dir():
            raise NotADirectoryError(f"{directory} is not a directory")

        plugins = []

        for item in directory.glob('*/*.py'):
            if item.is_file() and item.suffix == '.py' and item.name != '__init__.py' and not item.name.startswith('_'):
                try:
                    plugins.append(self.load_from_path(item))
                except (ImportError, FileNotFoundError) as e:
                    logger.exception(f"Failed to import {item}", exc_info=e)
                except Exception as e:
                    logger.exception(f"Unexpected error importing {item}", exc_info=e)

        return plugins

    def can_load(self, path: Path) -> bool:
        """Check if this loader can load the plugin at the given path."""
        return path.is_file() and path.suffix == '.py'


class PythonPackagePluginLoader:
    """Loader for Python package plugins."""

    def load_from_path(self, path: Path, name: Optional[str] = None) -> Plugin:
        """Load a plugin from a directory with an __init__.py file."""
        path = path.resolve()
        package_name = name or path.name

        # Ensure the package contains an __init__.py file
        init_file = path / '__init__.py'
        if not init_file.exists():
            raise ImportError(f"Cannot find __init__.py in package directory {path}")

        # Add the package path to sys.path to ensure all submodules can be imported
        sys.path.insert(0, str(path.parent))

        try:
            # Load the package
            spec = importlib.util.spec_from_file_location(package_name, init_file)
            if spec is None:
                raise ImportError(f"Failed to create module spec for {init_file}")

            package = importlib.util.module_from_spec(spec)

            if package_name in sys.modules:
                raise ImportError(f"Module {package_name} already exists")

            sys.modules[package_name] = package

            if spec.loader is None:
                raise ImportError(f"Module loader is None for {init_file}")

            spec.loader.exec_module(package)

            return PythonModulePlugin(package, path)
        finally:
            # Remove the package path from sys.path
            sys.path.pop(0)

    def load_all_from_directory(self, directory: Path) -> List[Plugin]:
        """Load all directories with __init__.py from a directory as plugins."""
        logger = logging.getLogger(__name__)
        directory = directory.resolve()

        if not directory.is_dir():
            raise NotADirectoryError(f"{directory} is not a directory")

        plugins = []

        for item in directory.glob('*/*/'):
            if item.is_dir() and (item / '__init__.py').exists() and not item.name.startswith('_'):
                try:
                    plugins.append(self.load_from_path(item))
                except (ImportError, FileNotFoundError) as e:
                    logger.exception(f"Failed to import {item}", exc_info=e)
                except Exception as e:
                    logger.exception(f"Unexpected error importing {item}", exc_info=e)

        return plugins

    def can_load(self, path: Path) -> bool:
        """Check if this loader can load the plugin at the given path."""
        return path.is_dir() and (path / '__init__.py').exists()
