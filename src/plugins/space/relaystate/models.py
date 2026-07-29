from datetime import datetime, UTC
from typing import Annotated

from beanie import Document, Indexed, before_event, Insert, Replace, Save, Update
from pydantic import BaseModel, Field


class RelayStateUpdateRequest(BaseModel):
    active: Annotated[bool, Field(description="Indicates whether the relay is active")]
    timestamp: Annotated[
        datetime,
        Field(description="The timestamp of the relay state update", examples=[datetime.now(UTC).isoformat()]),
    ]
    total_active_seconds: Annotated[
        int,
        Field(description="Total seconds the relay has been active", examples=[3600]),
    ]


class RelayStateResetRequest(BaseModel):
    timestamp: Annotated[
        datetime,
        Field(description="The timestamp of the relay reset request", examples=[datetime.now(UTC).isoformat()]),
    ]
    previous_total_active_seconds: Annotated[
        int,
        Field(description="Total seconds the relay was active before reset", examples=[3600]),
    ]


class RelayState(Document):
    """
    Stores the latest reported relay state for a device.
    """
    device: Annotated[str, Field(description="Device hostname"), Indexed(unique=True, name="device_unique")]
    active: Annotated[bool, Field(description="Whether the relay is currently active")]
    smibhid_timestamp: Annotated[datetime, Field(description="Timestamp supplied by SMIBHID")]
    total_active_seconds: Annotated[int, Field(description="SMIBHID-reported cumulative active seconds")]
    updated_at: Annotated[
        datetime,
        Field(default_factory=lambda: datetime.now(UTC), description="Timestamp of when SMIB last updated this state"),
    ]

    @before_event(Insert, Replace, Save, Update)
    def update_updated_at(self):
        self.updated_at = datetime.now(UTC)

    class Settings:
        name = "space_relay_state"


class RelayStateHistory(Document):
    """
    Stores the history of relay state transition events received from SMIBHID.
    """
    received_at: Annotated[
        datetime,
        Field(default_factory=lambda: datetime.now(UTC), description="Timestamp of when SMIB received the event"),
        Indexed(),
    ]
    device: Annotated[str, Field(description="Device hostname"), Indexed()]
    active: Annotated[bool, Field(description="Whether the relay became active")]
    smibhid_timestamp: Annotated[datetime, Field(description="Timestamp supplied by SMIBHID"), Indexed()]
    total_active_seconds: Annotated[int, Field(description="SMIBHID-reported cumulative active seconds")]

    class Settings:
        name = "space_relay_state_history"


class RelayResetHistory(Document):
    """
    Stores the history of relay on-time counter reset events received from SMIBHID.
    """
    received_at: Annotated[
        datetime,
        Field(default_factory=lambda: datetime.now(UTC), description="Timestamp of when SMIB received the reset event"),
        Indexed(),
    ]
    device: Annotated[str, Field(description="Device hostname"), Indexed()]
    smibhid_timestamp: Annotated[datetime, Field(description="Timestamp supplied by SMIBHID"), Indexed()]
    previous_total_active_seconds: Annotated[int, Field(description="SMIBHID total that was reset to zero")]

    class Settings:
        name = "space_relay_reset_history"