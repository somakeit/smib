import secrets
from pathlib import Path

from pydantic import computed_field, SecretStr, Field

from ._env_base_settings import EnvBaseSettings
from .project import ProjectSettings

class SlackSettings(EnvBaseSettings):
    bot_token: SecretStr
    app_token: SecretStr
    signing_secret: SecretStr = Field(default_factory=lambda: secrets.token_hex(16))



    model_config = {
        "env_prefix": "SMIB_SLACK_"
    }