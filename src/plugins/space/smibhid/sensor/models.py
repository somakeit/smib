from datetime import datetime, UTC
from typing import Annotated, Optional

import pymongo
from beanie import Document, Indexed
from beanie.odm.operators.update.general import Set
from pydantic import BaseModel, Field, AfterValidator, RootModel

from ..common import validate_timestamp


# --- RootModel wrappers for structured dicts ---

class SensorReading(RootModel):
    root: dict[str, int | float]

class SensorDataMap(RootModel):
    root: dict[str, SensorReading]

class SensorUnit_(RootModel):
    root: dict[str, str]

class SensorUnitMap(RootModel):
    root: dict[str, SensorUnit_]


# --- Models ---
class SensorLogBase(BaseModel):
    timestamp: Annotated[
        int | float,
        Field(description="Unix epoch timestamp", examples=[int(datetime.now(UTC).timestamp())]),
        AfterValidator(validate_timestamp)
    ]
    data: Annotated[
        SensorDataMap,
        Field(description="Sensor Data", examples=[{
            "SCD30": {
                "co2": 1548.1,
                "temperature": 26.3,
                "relative_humidity": 52.9
            },
            "BME280": {
                "pressure": 632,
                "humidity": 57.64,
                "temperature": 23.05
            }
        }])
    ]


class SensorLogReading(SensorLogBase):
    human_timestamp: Annotated[
        str,
        Field(description="Human readable timestamp",
              examples=[datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        (lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S%z")[:-2] + ":" + dt.strftime("%Y-%m-%dT%H:%M:%S%z")[-2:])(datetime.now(UTC))
                        ])
    ]

class SensorLogRequest(BaseModel):
    readings: list[SensorLogReading]
    units: Annotated[
        SensorUnitMap,
        Field(description="Sensor Units", examples=[{
            "SCD30": {
                "co2": "ppm",
                "temperature": "C",
                "relative_humidity": "%"
            },
            "BME280": {
                "pressure": "hPa",
                "humidity": "%",
                "temperature": "C"
            }
        }])
    ]

class SensorLog(Document, SensorLogBase):
    device: Annotated[str, Field(description="Device hostname")]
    timestamp: Annotated[datetime, Field(examples=[datetime.now(UTC)]), Indexed()]
    received_timestamp: Annotated[datetime, Field(examples=[datetime.now(UTC)], default_factory=lambda: datetime.now(UTC)), Indexed()]

    @classmethod
    def from_api(cls, api_model: SensorLogReading, device: str):
        return cls(
            timestamp=datetime.fromtimestamp(api_model.timestamp, UTC),
            data=api_model.data,
            device=device
        )

    @classmethod
    async def get_latest_log(cls, /,device: str | None = None) -> Optional["SensorLog"]:
        if device:
            return await cls.find_one(cls.device == device, sort=[(cls.timestamp, pymongo.DESCENDING)])
        return await cls.find_one(sort=[(cls.timestamp, pymongo.DESCENDING)])

    @classmethod
    async def get_latest_log_received(cls) -> Optional["SensorLog"]:
        return await cls.find_one(sort=[(cls.received_timestamp, pymongo.DESCENDING)])

    class Settings:
        name = "smibhid_sensor_log"

class SensorUnit(Document):
    device: Annotated[str, Field(description="Device hostname"), Indexed()]
    sensors: Annotated[SensorUnitMap, Field(description="Sensor Units", examples=[{
        "SCD30": {
            "co2": "ppm",
            "temperature": "C",
            "relative_humidity": "%"
        },
        "BME280": {
            "pressure": "hPa",
            "humidity": "%",
            "temperature": "C"
        }
    }])]

    created_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC), examples=[datetime.now(UTC)])]
    updated_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC), examples=[datetime.now(UTC)])]

    @classmethod
    async def upsert_from_api(cls, data: SensorUnitMap, device: str) -> "SensorUnit":
        return await cls.find_one(cls.device == device).upsert(
            Set({cls.sensors: data, cls.updated_at: datetime.now(UTC)}),
            on_insert=SensorUnit(device=device, sensors=data, updated_at=datetime.now(UTC), created_at=datetime.now(UTC))
        )

    @classmethod
    async def get_for_device(cls, /,device: str | None = None) -> Optional["SensorUnit"]:
        return await cls.find_one(cls.device == device)

    class Settings:
        name = "smibhid_sensor_units"

class SensorLogMonitorState(Document):
    last_log_received: Annotated[datetime | None, Field(default=None, examples=[datetime.now(UTC)])]
    last_check: Annotated[datetime | None, Field(default=None, examples=[datetime.now(UTC)])]
    last_alert_sent: Annotated[datetime | None, Field(default=None, examples=[datetime.now(UTC)])]
    alert_active: Annotated[bool, Field(default=False)]

    class Settings:
        name = "smibhid_sensor_log_monitor_state"

