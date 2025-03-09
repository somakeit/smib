from datetime import datetime
from datetime import UTC
from enum import StrEnum
from typing import Annotated

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, field_validator, BeforeValidator


def convert_timestamp(value: int | float | datetime) -> datetime:
    """Convert int timestamps to datetime."""
    if isinstance(value, float) or isinstance(value, int):
        try:
            return datetime.fromtimestamp(value, tz=UTC)
        except Exception as e:
            raise ValueError("Invalid timestamp value") from e
    elif isinstance(value, datetime):
        return value
    raise ValueError("Invalid timestamp value")


class UILogEventType(StrEnum):
    BUTTON_PRESS = 'button_press'

class ButtonPressEvent(BaseModel):
    button_name: str
    button_id: str


class UILog(Document):
    # Redefine mongodb default 'id' field to be excluded from the schema
    id: Annotated[PydanticObjectId | None, Field(default=None, description="MongoDB document ObjectID", exclude=True)]

    event: ButtonPressEvent
    type: UILogEventType
    timestamp: Annotated[datetime, BeforeValidator(convert_timestamp)]

    class Settings:
        name = "smibhid_ui_log"