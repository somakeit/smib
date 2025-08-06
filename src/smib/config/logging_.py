from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings as EnvBaseSettings

from ._env_base_settings import EnvBaseSettings


class LoggingSettings(EnvBaseSettings):
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level for the application (DEBUG, INFO, WARNING, ERROR)"
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper()
        return v

    model_config = {
        "env_prefix": "SMIB_LOGGING_"
    }
