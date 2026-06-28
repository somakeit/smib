from datetime import datetime, UTC
from typing import Annotated, Optional

import pymongo
from beanie import Document, Indexed
from beanie.odm.operators.update.general import Set
from pydantic import BaseModel, Field, AfterValidator, RootModel

from ..common import validate_timestamp


SENSOR_DATA_EXAMPLE = {
    "BH1750": {
        "light": 200.0
    },
    "BME280": {
        "pressure": 1020.2,
        "humidity": 39.55,
        "temperature": 29
    },
    "SCD30": {
        "co2": 480.2,
        "temperature": 30.4,
        "relative_humidity": 39.2
    },
    "PMSA003I": {
        "particles_100um": 0,
        "particles_05um": 232,
        "particles_10um": 30,
        "pm25_standard": 6,
        "particles_03um": 744,
        "pm10_standard": 5,
        "particles_25um": 0,
        "pm100_env": 6,
        "pm10_env": 5,
        "pm25_env": 6,
        "pm100_standard": 6,
        "particles_50um": 0
    }
}

SENSOR_UNITS_EXAMPLE = {
    "BH1750": {
        "light": "lx"
    },
    "BME280": {
        "pressure": "hPa",
        "temperature": "C",
        "humidity": "%"
    },
    "SCD30": {
        "relative_humidity": "%",
        "temperature": "C",
        "co2": "ppm"
    },
    "PMSA003I": {
        "particles_10um": "count/0.1L",
        "particles_05um": "count/0.1L",
        "particles_50um": "count/0.1L",
        "pm25_standard": "ug/m3",
        "particles_100um": "count/0.1L",
        "pm10_standard": "ug/m3",
        "particles_25um": "count/0.1L",
        "pm100_env": "ug/m3",
        "particles_03um": "count/0.1L",
        "pm25_env": "ug/m3",
        "pm100_standard": "ug/m3",
        "pm10_env": "ug/m3"
    }
}


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
        Field(description="Sensor Data", examples=[SENSOR_DATA_EXAMPLE])
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
    readings: Annotated[
        list[SensorLogReading],
        Field(description="Sensor readings", examples=[[
            {
                "timestamp": int(datetime.now(UTC).timestamp()),
                "human_timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "data": SENSOR_DATA_EXAMPLE
            }
        ]])
    ]
    units: Annotated[
        SensorUnitMap,
        Field(description="Sensor Units", examples=[SENSOR_UNITS_EXAMPLE])
    ]

class SensorLog(Document, SensorLogBase):
    """
    Stores recorded sensor readings from a S.M.I.B.H.I.D. device.
    """
    device: Annotated[str, Field(description="Device hostname", examples=["SMIBHID-DUMMY"])]
    timestamp: Annotated[datetime, Field(description="Timestamp of the sensor reading on the device", examples=[datetime.now(UTC)]), Indexed()]
    received_timestamp: Annotated[datetime, Field(description="Timestamp of when the sensor reading was received by S.M.I.B.", examples=[datetime.now(UTC)], default_factory=lambda: datetime.now(UTC)), Indexed()]

    @classmethod
    def from_api(cls, api_model: SensorLogReading, device: str):
        return cls(
            timestamp=datetime.fromtimestamp(api_model.timestamp, UTC),
            data=api_model.data,
            device=device
        )

    @classmethod
    async def get_latest_log(cls, /, device: str | None = None) -> Optional["SensorLog"]:
        if device:
            return await cls.find_one(cls.device == device, sort=[(cls.timestamp, pymongo.DESCENDING)])
        return await cls.find_one(sort=[(cls.timestamp, pymongo.DESCENDING)])

    @classmethod
    async def get_latest_log_received(cls) -> Optional["SensorLog"]:
        return await cls.find_one(sort=[(cls.received_timestamp, pymongo.DESCENDING)])

    class Config:
        json_schema_extra = {
            "example": {
                "device": "SMIBHID-DUMMY",
                "timestamp": datetime.now(UTC),
                "received_timestamp": datetime.now(UTC),
                "data": SENSOR_DATA_EXAMPLE
            }
        }

    class Settings:
        name = "smibhid_sensor_log"

class SensorUnit(Document):
    """
    Stores sensor unit information for a S.M.I.B.H.I.D. device.
    """
    device: Annotated[str, Field(description="Device hostname", examples=["SMIBHID-DUMMY"]), Indexed(unique=True, name="device_unique")]
    sensors: Annotated[
        SensorUnitMap,
        Field(description="Sensor Units", examples=[SENSOR_UNITS_EXAMPLE])
    ]

    created_at: Annotated[datetime, Field(description="Timestamp of when the sensor unit document was created", default_factory=lambda: datetime.now(UTC), examples=[datetime.now(UTC)])]
    updated_at: Annotated[datetime, Field(description="Timestamp of when the sensor unit document was last updated", default_factory=lambda: datetime.now(UTC), examples=[datetime.now(UTC)])]

    @classmethod
    async def upsert_from_api(cls, data: SensorUnitMap, device: str) -> "SensorUnit":
        return await cls.find_one(cls.device == device).upsert(
            Set({cls.sensors: data, cls.updated_at: datetime.now(UTC)}),
            on_insert=SensorUnit(device=device, sensors=data, updated_at=datetime.now(UTC), created_at=datetime.now(UTC))
        )

    @classmethod
    async def get_for_device(cls, /, device: str | None = None) -> Optional["SensorUnit"]:
        return await cls.find_one(cls.device == device)

    class Config:
        json_schema_extra = {
            "example": {
                "device": "SMIBHID-DUMMY",
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "sensors": SENSOR_UNITS_EXAMPLE
            }
        }

    class Settings:
        name = "smibhid_sensor_units"

class SensorLogMonitorState(Document):
    """
    Stores sensor log monitor state information.
    """
    last_log_received: Annotated[datetime | None, Field(description="Timestamp of the last sensor log received by S.M.I.B.", default=None, examples=[datetime.now(UTC)])]
    last_check: Annotated[datetime | None, Field(description="Timestamp of the last check for sensor logs by S.M.I.B.", default=None, examples=[datetime.now(UTC)])]
    last_alert_sent: Annotated[datetime | None, Field(description="Timestamp of the last alert sent by S.M.I.B.", default=None, examples=[datetime.now(UTC)])]
    alert_active: Annotated[bool, Field(description="Whether an alert is currently active", default=False, examples=[False])]

    class Settings:
        name = "smibhid_sensor_log_monitor_state"