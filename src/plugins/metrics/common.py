__display_name__ = "Metrics Common Stuff"
__description__ = "A plugin to hold common metrics stuff"
__author__ = "Sam Cork"

import logging

from pydantic import Field, SecretStr, field_validator, ValidationInfo

from smib.config import EnvBaseSettings
from smib.config.utils import init_plugin_settings


class MetricsCommonConfig(EnvBaseSettings):
    enabled: bool = Field(default=False, description="Global toggle for metrics")

    influx_url: str = Field(default="http://localhost:8086", description="InfluxDB URL for metrics storage")
    influx_token: SecretStr | None = Field(default=None, description="InfluxDB token for metrics storage")
    influx_org: str = Field(default="somakeit", description="InfluxDB organization for metrics storage")
    influx_bucket: str = Field(default="smib_metrics", description="InfluxDB bucket for metrics storage")

    model_config = {
        "env_prefix": "SMIB_METRICS_",
    }

    @field_validator("influx_token")
    @classmethod
    def validate_token_if_enabled(cls, v: SecretStr | None, info: ValidationInfo) -> SecretStr | None:
        # Check the 'enabled' field from the values already processed
        if info.data.get("enabled") and (v is None or not v.get_secret_value()):
            raise ValueError("must be provided when metrics are enabled")
        return v

_logger = logging.getLogger("Metrics Common Config")
config = init_plugin_settings(MetricsCommonConfig, _logger)