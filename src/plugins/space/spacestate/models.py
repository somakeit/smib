from datetime import datetime, UTC
from enum import StrEnum
from typing import Annotated

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class SpaceStateEnum(StrEnum):
    OPEN = "open"
    CLOSED = "closed"

class SpaceStateSource(StrEnum):
    HTTP = "http"
    SLACK = "slack"


class SpaceStateBase(BaseModel):
    open: Annotated[bool | None, Field(default=None, description="Whether the space is open")]

class SpaceState(Document, SpaceStateBase):
    """
    Stores the current space state.
    This collection should only ever have 1 document in it.
    """
    class Settings:
        name = "space_state"

class SpaceStateResponse(SpaceStateBase):
    pass

class SpaceStateHistory(Document):
    """
    Stores the history of space state changes.
    """
    timestamp: Annotated[datetime, Field(description="Timestamp of when the space state change was recorded", default_factory=lambda: datetime.now(UTC), examples=[datetime.now(UTC)]), Indexed()]
    open: Annotated[bool, Field(description="Whether the space is open")]

    class Settings:
        name = "space_state_history"

class SpaceStateEventHistory(Document):
    """
    Stores the history of space state events.
    """
    timestamp: Annotated[datetime, Field(description="Timestamp of when the space state event was recorded", default_factory=lambda: datetime.now(UTC), examples=[datetime.now(UTC)]), Indexed()]
    source: Annotated[SpaceStateSource, Field(description="The source of the event")]
    requested_state: Annotated[SpaceStateEnum, Field(description="The requested state")]
    requested_duration_seconds: Annotated[int | None, Field(default=None, description="The requested duration (in seconds)")]
    previous_state: Annotated[SpaceStateEnum | None, Field(default=None, description="The previous state")]
    new_state: Annotated[SpaceStateEnum, Field(description="The new state")]
    metrics_exported_at: Annotated[datetime | None, Field(default=None, description="Timestamp of when the metrics were exported"), Indexed()]

    class Settings:
        name = "space_state_event_history"


class SpaceStateOpen(BaseModel):
    hours: Annotated[int | None, Field(gt=-1, default=None, description="How many hours the space is open for?")]

class SpaceStateClosed(BaseModel):
    minutes: Annotated[int | None, Field(gt=-1, default=None, description="How many minutes the space is temporarily closed for?")]