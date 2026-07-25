from functools import cached_property
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import computed_field, Field, ValidateAs
from tzlocal import get_localzone_name

from ._env_base_settings import EnvBaseSettings
from .project import ProjectSettings


class GeneralSettings(EnvBaseSettings):
    timezone: Annotated[str, ValidateAs(ZoneInfo, str), Field(
        default_factory=get_localzone_name,
        description="Application timezone used for local date/time calculations. Defaults to the system timezone if not set.",
        examples=["Etc/UTC", "America/New_York", "Europe/London"]
    )]

    @computed_field
    @cached_property
    def plugins_directory(self) -> Path:
        return ProjectSettings().package_root.parent / "plugins"
