from dataclasses import dataclass
from pathlib import Path
from .plugin_type import PluginType


@dataclass
class PluginMeta:
    name: str
    description: str | None = None
    author: str | None = None


@dataclass
class Plugin:
    type: PluginType
    directory: Path
    id: str
    id_file: Path
    _base_directory: Path
    enabled: bool
    metadata: PluginMeta | None = None
    error: str | None = None
