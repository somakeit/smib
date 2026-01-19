__display_name__ = "Metrics Common Stuff"
__description__ = "A plugin to hold common metrics stuff"
__author__ = "Sam Cork"

import logging

from pydantic import Field, SecretStr, model_validator

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

    @model_validator(mode="after")
    def validate_token_if_enabled(self) -> MetricsCommonConfig:
        if self.enabled and not self.influx_token.get_secret_value():
            raise ValueError("influx_token must be provided when metrics are enabled")
        return self

_logger = logging.getLogger("Metrics Common Config")
config = init_plugin_settings(MetricsCommonConfig, _logger)