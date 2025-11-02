from enum import StrEnum

from pydantic import Field

from ._env_base_settings import EnvBaseSettings


class Environment(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class EnvironmentSettings(EnvBaseSettings):
    environment: Environment = Field(
        Environment.PRODUCTION,
        description="The application environment.",
    )
