import logging

from pydantic import Field, ValidationError
from smib.config import EnvBaseSettings, format_validation_errors
from smib.config._utils import init_plugin_settings


class SpaceStatePluginConfig(EnvBaseSettings):
    space_open_announce_channel_id: str = Field(
        default="space-open-announce",
        description="Slack channel ID where space open/close announcements are posted"
    )

    model_config = {
        "env_prefix": "SMIB_PLUGIN_SPACE_STATE_"
    }

_logger = logging.getLogger("Space State Plugin Config")
config = init_plugin_settings(SpaceStatePluginConfig, _logger)

