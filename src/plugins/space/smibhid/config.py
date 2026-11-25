"""
Per-device settings shared by every plugin that renders S.M.I.B.H.I.D. data.

A device's friendly name, where it belongs in an ordered readout, and how long its readings
stay trustworthy are facts about the device, not about any one plugin. /howfresh and the App
Home light state both need all four, and a device named "Clean Room" in one readout should
not appear as a bare hostname in the other - so they live here rather than in whichever
plugin happened to need them first.
"""

import logging
from datetime import timedelta

from pydantic import BaseModel, Field

from smib.config import EnvBaseSettings, IntervalField
from smib.config.utils import init_plugin_settings


def normalize_device_key(device: str) -> str:
    """
    Normalise a device hostname into the key form used by the per-device override map.

    Needed on both sides of the lookup. pydantic-settings lowercases the keys it parses out of
    env vars, and a hostname like `SMIBHID-FAN` cannot carry its hyphen reliably through the
    `DEVICE__<KEY>__<FIELD>` form, so case and hyphen/underscore are folded together. This
    means `SMIBHID-FAN`, `smibhid_fan` and `SMIBHID_FAN` all resolve to the same entry.
    """
    return device.strip().lower().replace("-", "_")


class SmibhidDeviceConfig(BaseModel):
    """
    Per-device overrides. Every field is optional - set only what differs for that device,
    and anything left unset falls back to the plugin-wide default.
    """

    name: str | None = Field(
        default=None,
        description="Friendly name shown instead of the device hostname, e.g. 'Clean Room'",
    )

    order: int | None = Field(
        default=None,
        description=(
            "Position in an ordered readout, lowest first. Devices without an order follow "
            "those that have one, sorted by name."
        ),
    )

    stale_after: IntervalField | None = Field(
        default=None,
        description="Overrides the global stale_after for this device",
    )

    exclude_after: IntervalField | None = Field(
        default=None,
        description="Overrides the global exclude_after for this device",
    )


class SmibhidDevicesConfig(EnvBaseSettings):
    stale_after: IntervalField = Field(
        default=timedelta(hours=1),
        description=(
            "Readings older than this are still shown, but marked as possibly stale. Accepts "
            "seconds (int), 'HH:MM:SS', or ISO8601 durations like 'PT1H'. Defaults to the same "
            "hour as the sensor log monitor's alert threshold, so a device is flagged at the "
            "point SMIB would already be alerting that it has stopped reporting."
        ),
    )

    exclude_after: IntervalField | None = Field(
        default=timedelta(days=2),
        description=(
            "Readings older than this are left out of a readout entirely, on the grounds that a "
            "device silent this long has been unplugged or reflashed rather than being briefly "
            "offline. A device is only ever dropped while another is still reporting - if every "
            "device is this stale they are all shown, marked, since a stale readout beats no "
            "readout. Accepts seconds (int), 'HH:MM:SS', or ISO8601 durations like 'P2D'. Set to "
            "None to never drop a device."
        ),
    )

    device: dict[str, SmibhidDeviceConfig] = Field(
        default_factory=dict,
        description=(
            "Per-device overrides keyed on device hostname, e.g. "
            "DEVICE__SMIBHID_FAN__NAME=Clean Room. Devices with no entry use the defaults "
            "above, so this can be left empty."
        ),
    )

    model_config = {
        **EnvBaseSettings.model_config,
        "env_prefix": "SMIB_PLUGIN_SMIBHID_DEVICES_",
        "env_nested_delimiter": "__",
    }

    def for_device(self, device: str) -> SmibhidDeviceConfig:
        return self.device.get(normalize_device_key(device)) or SmibhidDeviceConfig()

    def display_name(self, device: str) -> str:
        """The configured friendly name, falling back to the raw hostname."""
        return self.for_device(device).name or device

    def sort_key_for(self, device: str) -> tuple[int, int, str]:
        """
        Stable ordering for a multi-device readout.

        Without this, devices fall out in whatever order the query returned - which is
        usually by reading time, so they would reorder between renders as devices report.
        Devices with a configured order come first, lowest first; the rest follow, sorted by
        display name so the result is at least deterministic and matches what the reader sees.
        """
        order = self.for_device(device).order
        name = self.display_name(device).casefold()

        if order is None:
            return (1, 0, name)

        return (0, order, name)

    def stale_after_for(self, device: str) -> timedelta:
        return self.for_device(device).stale_after or self.stale_after

    def exclude_after_for(self, device: str) -> timedelta | None:
        override = self.for_device(device).exclude_after
        return override if override is not None else self.exclude_after


_logger = logging.getLogger("S.M.I.B.H.I.D. Devices Config")
config = init_plugin_settings(SmibhidDevicesConfig, _logger)
