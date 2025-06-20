from abc import ABC, abstractmethod, ABCMeta
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Union

from smib.utilities.dynamic_caller import dynamic_caller


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    display_name: str
    description: str
    author: Optional[str] = None

class Plugin(ABC, metaclass=ABCMeta):
    """Protocol defining the interface for plugins."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get the plugin's metadata."""
        pass

    @property
    @abstractmethod
    def path(self) -> Path:
        """Get the plugin's path."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the plugin's name."""
        pass

    @property
    @abstractmethod
    def unique_name(self) -> str:
        """Get the plugin's unique name."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        pass

    @abstractmethod
    def register(self, **kwargs: Any) -> None:
        """Register the plugin with the system."""
        pass

    def __lt__(self, other: "Plugin") -> bool:
        if not isinstance(other, Plugin):
            return NotImplemented
        return f"{self.category}\\{self.name}" < f"{other.category}\\{other.name}"


class PythonModulePlugin(Plugin):
    """Adapter for Python module plugins."""
    
    def __init__(self, module: ModuleType, path: Path):
        self._module = module
        self._path = path
        self._metadata = self._extract_metadata(module)
    
    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata
    
    @property
    def path(self) -> Path:
        return self._path
    
    @property
    def name(self) -> str:
        from smib.utilities.package import get_actual_module_name
        return get_actual_module_name(self._module)
    
    @property
    def unique_name(self) -> str:
        return self._module.__name__

    @property
    def category(self) -> str:
        return self._path.parent.name
    
    def register(self, **kwargs: Any) -> None:
        """Register the plugin by calling its register function."""
        if hasattr(self._module, 'register') and callable(self._module.register):
            dynamic_caller(self._module.register, **kwargs)
    
    @staticmethod
    def _extract_metadata(module: ModuleType) -> PluginMetadata:
        """Extract metadata from a Python module."""
        display_name = getattr(module, '__display_name__', None)
        description = getattr(module, '__description__', None)
        author = getattr(module, '__author__', None)
        
        return PluginMetadata(
            display_name=display_name,
            description=description,
            author=author
        )