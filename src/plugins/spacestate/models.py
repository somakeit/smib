from typing import Optional, Annotated

from beanie import Document, PydanticObjectId
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict, with_config


class SpaceState(Document):
    # Redefine mongodb default 'id' field to be excluded from the schema
    id: Annotated[PydanticObjectId | None, Field(default=None, description="MongoDB document ObjectID", exclude=True)]
    open: Annotated[bool | None, Field(default=None, description="Whether the space is open")]

    class Settings:
        name = "space_state"


class SpaceStateOpen(BaseModel):
    hours: Annotated[int | None, Field(gt=0, default=None, description="How many hours the space is open for?")]