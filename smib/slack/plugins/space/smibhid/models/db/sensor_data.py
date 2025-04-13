from datetime import datetime
from smib.slack.db import Model, Field


class SensorLog(Model):
    _name = "smibhid-sensor-logs"

    timestamp = Field[datetime](datetime, required=True)
    data = Field[dict[str, dict[str, float | int]]](dict, required=True)
    device_hostname = Field[str](str)
    device_ip = Field[str](str, required=True)
