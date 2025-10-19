from datetime import datetime, UTC
from enum import StrEnum
from typing import Annotated

from beanie import Document, Indexed
from pydantic import BaseModel, Field, AfterValidator

from ..common import validate_timestamp


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
    device: Annotated[str, Field(description="Device hostname")]

    timestamp: Annotated[datetime, Field(examples=[datetime.now(UTC)]), Indexed()]
    received_timestamp: Annotated[datetime, Field(examples=[datetime.now(UTC)], default_factory=lambda: datetime.now(UTC)), Indexed()]

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