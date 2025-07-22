from pydantic import Field

from ._env_base_settings import EnvBaseSettings


class LoggingSettings(EnvBaseSettings):
    log_level: str = Field(
        default="INFO",
        description="Logging level for the application (DEBUG, INFO, WARNING, ERROR)"
    )
    model_config = {
        "env_prefix": "SMIB_LOGGING_"
    }
