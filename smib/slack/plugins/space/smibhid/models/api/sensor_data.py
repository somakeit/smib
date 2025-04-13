from pydantic import BaseModel
from typing import Any


class SensorLog(BaseModel):
    # Represents one log entry with dynamic sensor names
    timestamp: int
    human_timestamp: str
    data: dict[str, dict[str, float | int]]  # Dynamic mapping of sensor name to SensorData


class SensorLogs(BaseModel):
    # A collection of log entries
    logs: list[SensorLog]

    def __iter__(self):
        yield from self.logs
