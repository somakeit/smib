from pydantic import BaseModel


class Version(BaseModel):
    smib: str
    python: str