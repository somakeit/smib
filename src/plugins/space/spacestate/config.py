import logging

from pydantic import Field

from smib.config import EnvBaseSettings
from smib.config.utils import init_plugin_settings


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

