from typing import Annotated

from pydantic import BaseModel, Field


class Version(BaseModel):
    smib: Annotated[str, Field(..., examples=["2.0.0"])]
    python: Annotated[str, Field(..., examples=["3.13.2"])]