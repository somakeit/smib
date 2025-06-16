from pydantic import BaseModel, Field


class Versions(BaseModel):
    smib: str