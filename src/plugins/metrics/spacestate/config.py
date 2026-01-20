import logging
from datetime import timedelta
from typing import Annotated

from pydantic import Field

from smib.config import EnvBaseSettings, IntervalField
from smib.config.utils import init_plugin_settings


class MetricsSpaceStateConfig(EnvBaseSettings):
    monitor_interval: Annotated[IntervalField, Field(default=timedelta(minutes=1), description="Interval between metric collection checks")]

    model_config = {
        "env_prefix": "SMIB_METRICS_SPACESTATE_",
    }

_logger = logging.getLogger("Space State Metrics Plugin Config")
config = init_plugin_settings(MetricsSpaceStateConfig, _logger)