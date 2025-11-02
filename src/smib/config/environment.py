from enum import StrEnum

from pydantic import Field, field_validator

from ._env_base_settings import EnvBaseSettings


class Environment(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"
    TESTING = "TESTING"

class EnvironmentSettings(EnvBaseSettings):
    environment: Environment = Field(
        Environment.PRODUCTION,
        description="The application environment.",
    )

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper()
        return v
