from datetime import datetime, UTC
from typing import Annotated

from beanie import Document, Indexed, before_event, Insert, Replace, Update, Save
from pydantic import BaseModel, Field

from plugins.space.smibhid.common import SMIBHIDTimestamp


class RelayStateReport(BaseModel):
    active: Annotated[
        bool,
        Field(
            description="Whether the relay is currently on",
            examples=[True],
        )
    ]
    total_active_seconds: Annotated[
        float,
        Field(
            ge=0,
            description="Cumulative relay on-time in seconds since device reset, as reported by S.M.I.B.H.I.D. Cross-check value only, not authoritative.",
            examples=[42.5],
        )
    ]
    timestamp: Annotated[SMIBHIDTimestamp, Field(description="Timestamp of the relay state report", examples=[int(datetime.now(UTC).timestamp()), "2023-07-01T12:00:00Z"])]


class RelayResetReport(BaseModel):
    previous_total_active_seconds: Annotated[
        float,
        Field(
            ge=0,
            description="Cumulative on-time S.M.I.B.H.I.D. just zeroed out",
            examples=[82],
        )
    ]
    timestamp: Annotated[
        SMIBHIDTimestamp,
        Field(description="Timestamp of the reset", examples=["2026-07-23T14:42:29Z"])
    ]


class RelayState(Document):
    """
    Stores the latest reported relay state for a device, plus SMIB's own
    authoritative cumulative on-time computed from received transitions.
    """
    device: Annotated[str, Field(description="Device hostname"), Indexed(unique=True, name="device_unique")]
    active: Annotated[bool, Field(description="Whether the relay is currently on", examples=[True])]
    reported_total_active_seconds: Annotated[
        float,
        Field(
            ge=0,
            description="Last cumulative on-time reported by S.M.I.B.H.I.D. Cross-check value only, not authoritative.",
            examples=[42.5],
        )
    ]
    computed_total_active_seconds: Annotated[
        float,
        Field(
            ge=0,
            default=0.0,
            description="SMIB's own authoritative cumulative on-time, computed from ON/OFF durations across received transitions",
            examples=[42.5],
        )
    ]
    active_since: Annotated[
        datetime | None,
        Field(default=None, description="Timestamp of the most recent ON transition; None when the relay is off or unknown", examples=[datetime.now(UTC)])
    ]
    computed_total_active_seconds_at_last_reset: Annotated[
        float,
        Field(
            ge=0,
            default=0.0,
            description="Snapshot of computed_total_active_seconds at the moment of the last reset; the drift-check baseline",
            examples=[42.5],
        )
    ]
    last_reset_at: Annotated[
        datetime | None,
        Field(default=None, description="Timestamp of the last reset event", examples=[datetime.now(UTC)])
    ]
    last_reset_previous_total_active_seconds: Annotated[
        float | None,
        Field(default=None, description="S.M.I.B.H.I.D.'s previous_total_active_seconds from the last reset payload, kept for observability only", examples=[82])
    ]
    relay_lifetime_alert_sent: Annotated[
        bool,
        Field(default=False, description="Whether the current cycle's relay-lifetime alert has fired at least once")
    ]
    relay_lifetime_alert_last_sent_at: Annotated[
        datetime | None,
        Field(default=None, description="Timestamp the relay-lifetime Slack alert was last actually sent", examples=[datetime.now(UTC)])
    ]
    drift_alert_active: Annotated[
        bool,
        Field(default=False, description="Whether relay state total_active_seconds drift is currently over the warning threshold")
    ]
    drift_alert_last_sent_at: Annotated[
        datetime | None,
        Field(default=None, description="Timestamp the drift warning Slack alert was last actually sent", examples=[datetime.now(UTC)])
    ]
    updated_at: Annotated[datetime, Field(description="Timestamp of when the relay state was last updated", default_factory=lambda: datetime.now(UTC), examples=[datetime.now(UTC)])]

    @before_event(Insert, Replace, Save, Update)
    def update_updated_at(self):
        self.updated_at = datetime.now(UTC)

    class Settings:
        name = "space_relay_state"


class RelayStateHistory(Document):
    """
    Stores the history of reported relay state changes, alongside SMIB's
    computed cumulative on-time as of each event, for later comparison.
    """
    device: Annotated[str, Field(description="Device hostname")]
    timestamp: Annotated[datetime, Field(description="Timestamp of the relay state transition on the device", examples=[datetime.now(UTC)]), Indexed()]
    received_at: Annotated[datetime, Field(description="Timestamp of when the relay state report was received by S.M.I.B.", default_factory=lambda: datetime.now(UTC), examples=[datetime.now(UTC)]), Indexed()]
    active: Annotated[bool, Field(description="Whether the relay is currently on", examples=[True])]
    reported_total_active_seconds: Annotated[
        float,
        Field(ge=0, description="Cumulative on-time reported by S.M.I.B.H.I.D. for this event", examples=[42.5])
    ]
    computed_total_active_seconds: Annotated[
        float,
        Field(ge=0, description="SMIB's own computed cumulative on-time after processing this event", examples=[42.5])
    ]

    class Settings:
        name = "space_relay_state_history"


class RelayResetHistory(Document):
    """
    Stores the history of relay on-time counter resets (e.g. filter changes).
    """
    device: Annotated[str, Field(description="Device hostname")]
    timestamp: Annotated[datetime, Field(description="Timestamp of the reset", examples=[datetime.now(UTC)]), Indexed()]
    received_at: Annotated[datetime, Field(description="Timestamp of when the reset report was received by S.M.I.B.", default_factory=lambda: datetime.now(UTC), examples=[datetime.now(UTC)]), Indexed()]
    previous_total_active_seconds: Annotated[
        float,
        Field(ge=0, description="Cumulative on-time S.M.I.B.H.I.D. just zeroed out", examples=[82])
    ]
    computed_total_active_seconds_at_reset: Annotated[
        float,
        Field(ge=0, description="SMIB's own lifetime cumulative on-time at the moment of the reset", examples=[42.5])
    ]

    class Settings:
        name = "space_relay_state_reset_history"
