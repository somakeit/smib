from beanie import Document
from bson import ObjectId
from pydantic import BaseModel


class SpaceState(BaseModel):
    open: bool | None = None

class SpaceStateDB(Document, SpaceState):

    class Settings:
        name = "space_state"