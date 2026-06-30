from datetime import datetime, UTC
from typing import Annotated

from beanie import Document, Indexed, before_event, Insert, Replace, Update, Save
from pydantic import BaseModel, Field
import pymongo


class SpaceLightStateBase(BaseModel):
    light_state: Annotated[
        bool,
        Field(
            description="Whether the reported light level is above the configured threshold",
            examples=[True],
        )
    ]
    light_value_lux: Annotated[
        float,
        Field(
            ge=0,
            description="Reported light level in lux",
            examples=[591.67],
        )
    ]
    threshold_lux: Annotated[
        float,
        Field(
            ge=0,
            description="Configured light threshold in lux",
            examples=[500],
        )
    ]


class SpaceLightState(Document, SpaceLightStateBase):
    """
    Stores the latest reported light-derived state for a device.
    """
    device: Annotated[str, Field(description="Device hostname"), Indexed(unique=True, name="device_unique")]
    updated_at: Annotated[datetime, Field(description="Timestamp of when the light state was last updated", default_factory=lambda: datetime.now(UTC), examples=[datetime.now(UTC)])]

    @before_event(Insert, Replace, Save, Update)
    def update_updated_at(self):
        self.updated_at = datetime.now(UTC)

    @classmethod
    async def get_latest_state(cls) -> SpaceLightState | None:
        return await cls.find_one(sort=[(cls.updated_at, pymongo.DESCENDING)])

    class Settings:
        name = "space_light_state"


class SpaceLightStateResponse(SpaceLightStateBase):
    device: Annotated[str, Field(description="Device hostname")]
    updated_at: Annotated[datetime, Field(description="Timestamp of when the light state was last updated")]


class SpaceLightStateHistory(Document, SpaceLightStateBase):
    """
    Stores the history of reported light-derived state changes.
    """
    timestamp: Annotated[datetime, Field(description="Timestamp of when the light state report was recorded", default_factory=lambda: datetime.now(UTC), examples=[datetime.now(UTC)]), Indexed()]
    device: Annotated[str, Field(description="Device hostname")]

    class Settings:
        name = "space_light_state_history"


class SpaceLightStateReport(SpaceLightStateBase):
    pass