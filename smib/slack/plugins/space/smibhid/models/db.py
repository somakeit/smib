from datetime import datetime
from typing import Any

from smib.slack.db import Model, Field

from pydantic import BaseModel


class UILog(Model):
    _name = "smibhid-ui-logs"

    timestamp = Field[datetime](datetime)
    type = Field[str](str, required=True)
    event = Field[dict](dict, required=True)
    device_hostname = Field[str](str)
    device_ip = Field[str](str, required=True)
