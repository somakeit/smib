import secrets
from typing import ClassVar

from pydantic import SecretStr, Field, field_validator

from ._env_base_settings import EnvBaseSettings


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

    _BOT_TOKEN_PREFIX: ClassVar[str] = "xoxb-"
    _APP_TOKEN_PREFIX: ClassVar[str] = "xapp-"

    @staticmethod
    def _get_str(v):
        return v.get_secret_value() if isinstance(v, SecretStr) else v

    @staticmethod
    def _validate_prefix(value, prefix: str, kind: str):
        s = SlackSettings._get_str(value)
        if not isinstance(s, str):
            return value
        if not s.startswith(prefix):
            raise ValueError(f"Invalid Slack {kind} format (expected prefix {prefix})")
        return value

    @field_validator("bot_token", mode="before")
    @classmethod
    def validate_bot_token(cls, v):
        return cls._validate_prefix(v, cls._BOT_TOKEN_PREFIX, "bot token")

    @field_validator("app_token", mode="before")
    @classmethod
    def validate_app_token(cls, v):
        return cls._validate_prefix(v, cls._APP_TOKEN_PREFIX, "app token")

    model_config = {
        "env_prefix": "SMIB_SLACK_"
    }
