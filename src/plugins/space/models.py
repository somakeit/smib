from typing import Optional, Annotated

from beanie import Document, PydanticObjectId
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict, with_config


class SpaceState(Document):
    # Redefine mongodb default 'id' field to be excluded from the schema
    id: Annotated[Optional[PydanticObjectId], Field(default=None, description="MongoDB document ObjectID", exclude=True)]
    open: bool | None = None

    class Settings:
        name = "space_state"
