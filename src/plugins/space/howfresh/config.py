import logging
from datetime import timedelta

from pydantic import BaseModel, Field

from smib.config import EnvBaseSettings, IntervalField
from smib.config.utils import init_plugin_settings

HOW_FRESH_USERNAME = "How Fresh?"
HOW_FRESH_PICTURE = (
    "https://imgix.bustle.com/uploads/image/2018/5/11/8f6aebb3-90cc-4e5f-b153-96a21a765342-will-smith-fresh-prince-um-maluco-no-pedaco-netflix-xlarge_trans_nvbqzqnjv4bqnjjoebt78qiaydkjdey4cngtjfjs74myhny6w3gnbo8.jpg?w=350&h=350&fit=crop&crop=faces&dpr=2"
)

HOW_FRESH_PROFILE = {
    "username": HOW_FRESH_USERNAME,
    "icon_url": HOW_FRESH_PICTURE,
}


def normalize_device_key(device: str) -> str:
    """
    Normalise a device hostname into the key form used by the per-device override map.

    Needed on both sides of the lookup. pydantic-settings lowercases the keys it parses out of
    env vars, and a hostname like `SMIBHID-FAN` cannot carry its hyphen reliably through the
    `DEVICE__<KEY>__<FIELD>` form, so case and hyphen/underscore are folded together. This
    means `SMIBHID-FAN`, `smibhid_fan` and `SMIBHID_FAN` all resolve to the same entry.
    """
    return device.strip().lower().replace("-", "_")


class HowFreshDeviceConfig(BaseModel):
    """
    Per-device overrides. Every field is optional - set only what differs for that device,
    and anything left unset falls back to the plugin-wide default.
    """

    name: str | None = Field(
        default=None,
        description="Friendly name shown instead of the device hostname, e.g. 'Clean Room'",
    )

    stale_after: IntervalField | None = Field(
        default=None,
        description="Overrides the plugin-wide stale_after for this device",
    )

    exclude_after: IntervalField | None = Field(
        default=None,
        description="Overrides the plugin-wide exclude_after for this device",
    )


class HowFreshPluginConfig(EnvBaseSettings):
    stale_after: IntervalField = Field(
        default=timedelta(hours=1),
        description=(
            "Readings older than this are still shown, but marked as possibly stale. Accepts "
            "seconds (int), 'HH:MM:SS', or ISO8601 durations like 'PT1H'. Defaults to the same "
            "hour as the sensor log monitor's alert threshold, so /howfresh flags a device at "
            "the point SMIB would already be alerting that it has stopped reporting."
        ),
    )

    exclude_after: IntervalField | None = Field(
        default=timedelta(days=2),
        description=(
            "Readings older than this are left out of the readout entirely, on the grounds that "
            "a device silent this long has been unplugged or reflashed rather than being briefly "
            "offline. A device is only ever dropped while another is still reporting - if every "
            "device is this stale they are all shown, marked, since a stale readout beats no "
            "readout. Accepts seconds (int), 'HH:MM:SS', or ISO8601 durations like 'P2D'. Set to "
            "None to never drop a device."
        ),
    )

    device: dict[str, HowFreshDeviceConfig] = Field(
        default_factory=dict,
        description=(
            "Per-device overrides keyed on device hostname, e.g. "
            "DEVICE__SMIBHID_FAN__NAME=Clean Room. Devices with no entry use the defaults "
            "above, so this can be left empty."
        ),
    )

    model_config = {
        **EnvBaseSettings.model_config,
        "env_prefix": "SMIB_PLUGIN_SPACE_HOW_FRESH_",
        "env_nested_delimiter": "__",
    }

    def for_device(self, device: str) -> HowFreshDeviceConfig:
        return self.device.get(normalize_device_key(device)) or HowFreshDeviceConfig()

    def display_name(self, device: str) -> str:
        """The configured friendly name, falling back to the raw hostname."""
        return self.for_device(device).name or device

    def stale_after_for(self, device: str) -> timedelta:
        return self.for_device(device).stale_after or self.stale_after

    def exclude_after_for(self, device: str) -> timedelta | None:
        override = self.for_device(device).exclude_after
        return override if override is not None else self.exclude_after


_logger = logging.getLogger(f"{HOW_FRESH_USERNAME} Plugin Config")
config = init_plugin_settings(HowFreshPluginConfig, _logger)
