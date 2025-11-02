from functools import cached_property
from pathlib import Path

from pydantic import computed_field

from ._env_base_settings import EnvBaseSettings
from .project import ProjectSettings


class GeneralSettings(EnvBaseSettings):
    @computed_field
    @cached_property
    def plugins_directory(self) -> Path:
        return ProjectSettings().package_root.parent / "plugins"
