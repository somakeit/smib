from dataclasses import dataclass, asdict
from pathlib import Path
from .plugin_type import PluginType
from smib.slack.config import ROOT_DIRECTORY


@dataclass
class PluginMeta:
    name: str
    description: str | None = None
    author: str | None = None

    def __dict__(self) -> dict:
        return asdict(self)


@dataclass
class Plugin:
    type: PluginType
    group: str
    directory: Path
    id: str
    id_file: Path
    _base_directory: Path
    enabled: bool
    metadata: PluginMeta | None = None
    error: str | None = None

    def __dict__(self) -> dict:
        return asdict(self)

    def to_json_dict(self) -> dict:
        return {
            "type": self.type.value,
            "group": self.group,
            "directory": self.directory.relative_to(ROOT_DIRECTORY.parent).as_posix(),
            "id": self.id,
            "id_file": self.id_file.relative_to(ROOT_DIRECTORY.parent).as_posix(),
            "base_directory": self._base_directory.relative_to(ROOT_DIRECTORY.parent).as_posix(),
            "enabled": self.enabled,
            "metadata": self.metadata.__dict__() if self.metadata else None,
            "error": self.error
        }
