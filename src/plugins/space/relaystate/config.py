import logging
from datetime import timedelta

from pydantic import Field

from smib.config import EnvBaseSettings, IntervalField
from smib.config.utils import init_plugin_settings


class RelayStatePluginConfig(EnvBaseSettings):
    """
    Note: this config is global, not per-device. Every SMIBHID device gets its own RelayState
    document, but these thresholds/channels/relay_name/message template apply uniformly across
    all of them. See https://github.com/somakeit/smib/issues/510 for the broader multi-SMIBHID
    configuration discussion.
    """

    total_active_seconds_drift_warning_threshold_seconds: float = Field(
        default=300,
        description="Log a warning when SMIB's computed cumulative relay on-time and S.M.I.B.H.I.D.'s reported total_active_seconds differ by more than this many seconds",
    )

    monitor_interval: IntervalField | None = Field(
        default=timedelta(minutes=5),
        description="Interval between periodic sweeps of all known relay states, re-checking drift and relay-lifetime thresholds independent of new incoming reports (catches e.g. a relay stuck ON with no new events landing). Accepts seconds (int), 'HH:MM:SS', or ISO8601 durations like 'PT5M'. If None, only event-triggered checks run.",
    )

    relay_lifetime_warning_threshold: IntervalField | None = Field(
        default=None,
        description="On-time (since the last reset) after which a relay-lifetime alert is sent. Accepts seconds (int), 'HH:MM:SS', or ISO8601 durations like 'P30D'. If None, relay-lifetime alerting is disabled.",
    )

    relay_lifetime_alert_channel_id: str = Field(
        default="code",
        description="Slack channel ID where relay-lifetime alerts are posted",
    )

    relay_lifetime_alert_resend_interval: IntervalField | None = Field(
        default=None,
        description="Interval to resend the relay-lifetime Slack alert while on-time since reset remains over threshold. Accepts seconds (int), 'HH:MM:SS', or ISO8601 durations. If None, the alert is only sent once per cycle.",
    )

    relay_name: str = Field(
        default="Relay",
        description="Friendly name for the tracked relay/filter, used in the alert message",
    )

    relay_lifetime_alert_message_template: str = Field(
        default=":warning: {relay_name} on {device} has been active for {duration} since the last reset, exceeding the {threshold} threshold — {relay_name} may need replacing.",
        description="Slack alert message template. Supports {device}, {relay_name}, {duration}, {threshold} placeholders.",
    )

    drift_warning_alert_channel_id: str = Field(
        default="code",
        description="Slack channel ID where relay state drift warnings are posted (independent of relay_lifetime_alert_channel_id)",
    )

    drift_warning_alert_resend_interval: IntervalField | None = Field(
        default=None,
        description="Interval to resend the drift warning Slack alert while drift remains over threshold. Accepts seconds (int), 'HH:MM:SS', or ISO8601 durations. If None, the alert is only sent once per drift episode.",
    )

    model_config = {
        "env_prefix": "SMIB_PLUGIN_SPACE_RELAY_STATE_"
    }

_logger = logging.getLogger("Space Relay State Plugin Config")
config = init_plugin_settings(RelayStatePluginConfig, _logger)
