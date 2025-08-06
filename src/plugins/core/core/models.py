from typing import Annotated

from pydantic import BaseModel, Field


class Versions(BaseModel):
    smib: Annotated[str, Field(description="SMIB version", examples=["2.0.0"])]
    mongo: Annotated[str, Field(description="MongoDB version", examples=["5.0.0"])]

class PingPong(BaseModel):
    ping: str = "pong"