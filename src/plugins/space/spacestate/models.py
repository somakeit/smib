from datetime import datetime, UTC
from enum import StrEnum
from typing import Annotated

from beanie import Document, PydanticObjectId, Indexed
from pydantic import BaseModel, Field


class SpaceStateEnum(StrEnum):
    OPEN = "open"
    CLOSED = "closed"

class SpaceStateSource(StrEnum):
    HTTP = "http"
    SLACK = "slack"

class SpaceState(Document):
    # Redefine mongodb default 'id' field to be excluded from the swagger schema
    id: Annotated[PydanticObjectId | None, Field(default=None, description="MongoDB document ObjectID", exclude=True)]
    open: Annotated[bool | None, Field(default=None, description="Whether the space is open")]

    class Settings:
        name = "space_state"

class SpaceStateHistory(Document):
    timestamp: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC)), Indexed()]
    open: Annotated[bool, Field(description="Whether the space is open")]

    class Settings:
        name = "space_state_history"

class SpaceStateEventHistory(Document):
    timestamp: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC)), Indexed()]
    source: Annotated[SpaceStateSource, Field(description="The source of the event")]
    requested_state: Annotated[SpaceStateEnum, Field(description="The requested state")]
    requested_duration_seconds: Annotated[int | None, Field(default=None, description="The requested duration (in seconds)")]
    previous_state: Annotated[SpaceStateEnum | None, Field(default=None, description="The previous state")]
    new_state: Annotated[SpaceStateEnum, Field(description="The new state")]

    class Settings:
        name = "space_state_event_history"


class SpaceStateOpen(BaseModel):
    hours: Annotated[int | None, Field(gt=-1, default=None, description="How many hours the space is open for?")]

class SpaceStateClosed(BaseModel):
    minutes: Annotated[int | None, Field(gt=-1, default=None, description="How many minutes the space is temporarily closed for?")]