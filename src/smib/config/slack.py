import secrets
from pathlib import Path

from pydantic import computed_field, SecretStr, Field

from ._env_base_settings import EnvBaseSettings
from .project import ProjectSettings

class SlackSettings(EnvBaseSettings):
    bot_token: SecretStr = Field(
        description="Slack bot token used for authentication with the Slack API"
    )
    app_token: SecretStr = Field(
        description="Slack app token used for socket mode connections"
    )
    signing_secret: SecretStr = Field(
        default_factory=lambda: secrets.token_hex(16),
        description="Secret used to verify requests from Slack"
    )



    model_config = {
        "env_prefix": "SMIB_SLACK_"
    }
