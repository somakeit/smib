from datetime import datetime, UTC
from enum import StrEnum
from typing import Annotated, Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, field_validator, field_serializer, ValidationError, BeforeValidator, \
    AfterValidator

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
    """API model with `timestamp` as an integer."""
    event: ButtonPressEvent
    type: UILogEventType
    timestamp: Annotated[int | float,
                        Field(description="Unix epoch timestamp", examples=[int(datetime.now(UTC).timestamp())]),
                        AfterValidator(validate_timestamp)
    ]


class UILog(Document, UILogCreate):
    """MongoDB document model, stores `timestamp` as `datetime`."""
    id: Annotated[PydanticObjectId | None, Field(default=None, exclude=True)]
    device: Annotated[str, Field(description="Device hostname")]

    timestamp: Annotated[datetime, Field(examples=[datetime.now(UTC)])]

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
