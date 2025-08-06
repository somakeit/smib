from pathlib import Path

from pydantic import computed_field
from pydantic_settings import (
    SettingsConfigDict,
    PyprojectTomlConfigSettingsSource,
    BaseSettings,
)

from smib.utilities.package import get_package_version, get_package_root

DEFAULT_VERSION = "0.0.0"

class _BaseProjectSettings(BaseSettings):
    name: str = ""
    description: str = ""
    version: str = DEFAULT_VERSION

    model_config = SettingsConfigDict(
        pyproject_toml_table_header=("project",),
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
    version: str = DEFAULT_VERSION
    display_name: str = ""

    model_config = SettingsConfigDict(extra="ignore")

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

    def model_post_init(self, __context):
        if self.version == "0.0.0":
            self.version = get_package_version(self.name)

    @computed_field
    @property
    def package_root(self) -> Path:
        return get_package_root(self.name)


if __name__ == "__main__":
    s = ProjectSettings()
    print(s.version.__dict__)
    print(s.model_dump())
