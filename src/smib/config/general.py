from functools import cached_property
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import computed_field, Field, ValidateAs

from ._env_base_settings import EnvBaseSettings
from .project import ProjectSettings


class GeneralSettings(EnvBaseSettings):
    timezone: Annotated[str, ValidateAs(ZoneInfo, str), Field(
        default="Europe/London",
        description="Application timezone used for local date/time calculations",
    )]

    @computed_field
    @cached_property
    def plugins_directory(self) -> Path:
        return ProjectSettings().package_root.parent / "plugins"
