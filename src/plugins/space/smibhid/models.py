from datetime import datetime, UTC
from enum import StrEnum
from typing import Annotated, Any

from beanie import Document, PydanticObjectId, Indexed
from pydantic import BaseModel, Field, AfterValidator


def validate_timestamp(value: Any) -> Any:
    """ Validate a timestamp."""
    if isinstance(value, (int, float)):
        try:
            datetime.fromtimestamp(value, UTC)
            return value
        except (OverflowError, OSError, ValueError):
            raise ValueError("Invalid Unix timestamp")
    raise ValueError("Timestamp must be an integer or float representing Unix time")


class UILogEventType(StrEnum):
    BUTTON_PRESS = 'button_press'


class ButtonPressEvent(BaseModel):
    button_name: Annotated[str, Field(description="Button name", examples=["Space Open"])]
    button_id: Annotated[str, Field(description="Button ID", examples=["space_open"])]


class UILogCreate(BaseModel):
    event: ButtonPressEvent
    type: UILogEventType
    timestamp: Annotated[int | float,
                        Field(description="Unix epoch timestamp", examples=[int(datetime.now(UTC).timestamp())]),
                        AfterValidator(validate_timestamp)
    ]


class UILog(Document, UILogCreate):
    id: Annotated[PydanticObjectId | None, Field(default=None, exclude=True)]
    device: Annotated[str, Field(description="Device hostname")]

    timestamp: Annotated[datetime, Field(examples=[datetime.now(UTC)]), Indexed()]

    @classmethod
    def from_api(cls, api_model: UILogCreate, device: str):
        return cls(
            event=api_model.event,
            type=api_model.type,
            timestamp=api_model.timestamp,
            device=device
        )

    class Settings:
        name = "smibhid_ui_log"

class SensorLogBase(BaseModel):
    timestamp: Annotated[int | float,
                        Field(description="Unix epoch timestamp", examples=[int(datetime.now(UTC).timestamp())]),
                        AfterValidator(validate_timestamp)
    ]
    data: Annotated[dict[str, dict[str, float | int]], Field(description="Sensor Data", examples=[
        {
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
        }
    ])]

class SensorLogCreate(SensorLogBase):
    human_timestamp: Annotated[str, Field(description="Human readable timestamp",
                                          examples=[datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")])
    ]

class SensorLog(Document, SensorLogBase):
    id: Annotated[PydanticObjectId | None, Field(default=None, exclude=True)]
    device: Annotated[str, Field(description="Device hostname")]

    timestamp: Annotated[datetime, Field(examples=[datetime.now(UTC)]), Indexed()]


    @classmethod
    def from_api(cls, api_model: SensorLogCreate, device: str):
        return cls(
            timestamp=api_model.timestamp,
            data=api_model.data,
            device=device
        )

    class Settings:
        name = "smibhid_sensor_log"