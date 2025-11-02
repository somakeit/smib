from functools import cached_property
from pathlib import Path

from packaging.version import Version
from pydantic import computed_field, field_validator, Field
from pydantic_settings import (
    SettingsConfigDict,
    PyprojectTomlConfigSettingsSource,
    BaseSettings,
)

from smib.utilities.package import get_package_version, get_package_root

DEFAULT_VERSION = Version("0.0.0")

class _BaseProjectSettings(BaseSettings):
    name: str = ""
    description: str = ""
    raw_version: Version = Field(DEFAULT_VERSION, alias="version")

    model_config = SettingsConfigDict(
        pyproject_toml_table_header=("project",),
        pyproject_toml_depth=3,
        extra="ignore",
        json_encoders={Version: str}
    )

    def model_post_init(self, __context):
        if self.raw_version == DEFAULT_VERSION:
            self.raw_version = Version(get_package_version(self.name))

    @field_validator("raw_version", mode="before")
    @classmethod
    def parse_version(cls, v):
        if isinstance(v, Version):
            return v
        return Version(v)

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls,
            init_settings,
            file_secret_settings,
            dotenv_settings,
            env_settings,
    ):
        return (PyprojectTomlConfigSettingsSource(cls),)


class _ToolSmibSettings(BaseSettings):
    display_name: str = ""

    model_config = SettingsConfigDict(
        pyproject_toml_table_header=("tool", "smib"),
        pyproject_toml_depth=3,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls,
            init_settings,
            file_secret_settings,
            dotenv_settings,
            env_settings,
    ):
        return (PyprojectTomlConfigSettingsSource(cls),)


class ProjectSettings(BaseSettings):
    name: str = ""
    description: str = ""
    raw_version: Version = Field(DEFAULT_VERSION, alias="version")
    display_name: str = ""

    model_config = SettingsConfigDict(extra="ignore", json_encoders={Version: str})

    def model_post_init(self, __context):
        if self.raw_version == DEFAULT_VERSION:
            self.raw_version = Version(get_package_version(self.name))

    @field_validator("raw_version", mode="before")
    @classmethod
    def parse_version(cls, v):
        if isinstance(v, Version):
            return v
        return Version(v)


    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls,
            init_settings,
            file_secret_settings,
            dotenv_settings,
            env_settings,
    ):
        project_source = PyprojectTomlConfigSettingsSource(_BaseProjectSettings)
        tool_smib_source = PyprojectTomlConfigSettingsSource(_ToolSmibSettings)

        def merged_source():
            proj_vals = project_source() or {}
            tool_vals = tool_smib_source() or {}
            return {**proj_vals, **tool_vals}

        return (merged_source, )

    @computed_field
    @cached_property
    def version(self) -> Version:
        from . import environment as environment_settings
        from .environment import Environment

        match environment_settings.environment:
            case Environment.PRODUCTION:
                return Version(self.raw_version.base_version)
            case Environment.DEVELOPMENT:
                return self.raw_version
            case Environment.TESTING:
                return Version(self.raw_version.public)

    @computed_field
    @cached_property
    def package_root(self) -> Path:
        return get_package_root(self.name)


if __name__ == "__main__":
    s = ProjectSettings()
    print(s.version.__dict__)
    print(s.model_dump())
