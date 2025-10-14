import logging

from pydantic import Field, ValidationError
from smib.config import EnvBaseSettings, format_validation_errors


class SpaceStatePluginConfig(EnvBaseSettings):
    space_open_announce_channel_id: str = Field(
        default="space-open-announce",
        description="Slack channel ID where space open/close announcements are posted"
    )

    model_config = {
        "env_prefix": "SMIB_PLUGIN_SPACE_STATE_"
    }

config = SpaceStatePluginConfig()

_logger = logging.getLogger("Space State Plugin Config")

try:
    config = SpaceStatePluginConfig()
except ValidationError as ve:
    errors = [(SpaceStatePluginConfig, ve),]
    msg = format_validation_errors(errors)
    _logger.error(msg)
    raise AssertionError('Invalid configuration') from ve

_logger.debug(f"\n{config.model_dump_json(indent=2)}")

