from pydantic import Field
from smib.config import EnvBaseSettings

class SpaceStatePluginConfig(EnvBaseSettings):
    space_open_announce_channel_id: str = Field(
        default="space-open-announce",
        description="Slack channel ID where space open/close announcements are posted"
    )

    model_config = {
        "env_prefix": "SMIB_PLUGIN_SPACE_STATE_"
    }

config = SpaceStatePluginConfig()
