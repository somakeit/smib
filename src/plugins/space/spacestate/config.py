from smib.config import EnvBaseSettings

class SpaceStatePluginConfig(EnvBaseSettings):
    space_open_announce_channel_id: str = "space-open-announce"

    model_config = {
        "env_prefix": "SMIB_PLUGIN_SPACE_STATE_"
    }

config = SpaceStatePluginConfig()