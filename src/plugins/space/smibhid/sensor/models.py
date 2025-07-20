from datetime import datetime, UTC
from typing import Annotated, Union

from beanie import Document, PydanticObjectId, Indexed
from beanie.odm.operators.update.general import Set
from pydantic import BaseModel, Field, AfterValidator, RootModel, ConfigDict

from ..common import validate_timestamp


# --- RootModel wrappers for structured dicts ---

class SensorReading(RootModel):
    root: dict[str, int | float]

class SensorDataMap(RootModel):
    root: dict[str, SensorReading]

class SensorUnit(RootModel):
    root: dict[str, str]

class SensorUnitMap(RootModel):
    root: dict[str, SensorUnit]


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
    id: Annotated[PydanticObjectId | None, Field(default=None, exclude=True)]
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

    class Settings:
        name = "smibhid_sensor_log"

class SensorUnits(Document):
    id: Annotated[PydanticObjectId | None, Field(default=None, exclude=True)]
    device: Annotated[str, Field(description="Device hostname"), Indexed()]
    sensors: Annotated[SensorUnitMap, Field(description="Sensor Units")]
    created_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    updated_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]

    @classmethod
    async def upsert_from_api(cls, data: SensorUnitMap, device: str) -> "SensorUnits":
        return await SensorUnits.find_one({"device": device}).upsert(
            Set({"sensors": data, "updated_at": datetime.now(UTC)}),
            on_insert=SensorUnits(device=device, sensors=data, updated_at=datetime.now(UTC), created_at=datetime.now(UTC))
        )

    class Settings:
        name = "smibhid_sensor_units"