import logging
from datetime import timedelta
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import SettingsConfigDict

from smib.config import EnvBaseSettings
from smib.config import format_validation_errors

class SmibhidSensorPluginConfig(EnvBaseSettings):
    monitor_interval: timedelta = Field(
        default=timedelta(minutes=1),
        description="Interval between sensor log monitor checks. Accepts seconds (int), 'HH:MM:SS', or ISO8601 durations like 'PT10M'."
    )

    monitor_alert_threshold: timedelta = Field(
        default=timedelta(hours=1),
        description="Interval between sensor log monitor alerts. Accepts seconds (int), 'HH:MM:SS', or ISO8601 durations like 'PT10M'."
    )

    monitor_alert_resend_interval: timedelta | None = Field(
        default=None,
        description="Interval to resend sensor log monitor alerts if the issue is not resolved. Accepts seconds (int), 'HH:MM:SS', or ISO8601 durations like 'PT10M'. If None, alerts are only sent once per issue."
    )

    monitor_alert_channel_id: str = Field(
        default="code",
        description="Slack channel ID where sensor log monitor alerts are posted"
    )

    model_config = {
        "env_prefix": "SMIB_PLUGIN_SMIBHID_SENSOR_"
    }
    SettingsConfigDict()


_logger = logging.getLogger("S.M.I.B.H.I.D. Sensor Plugin Config")

try:
    config = SmibhidSensorPluginConfig()
except ValidationError as ve:
    errors = [(SmibhidSensorPluginConfig, ve),]
    msg = format_validation_errors(errors)
    _logger.error(msg)
    raise AssertionError('Invalid configuration') from ve

_logger.debug(f"\n{config.model_dump_json(indent=2)}")

