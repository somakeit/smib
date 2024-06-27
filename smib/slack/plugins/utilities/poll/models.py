from datetime import datetime
from typing import Self

from smib.slack.db import Model, Field
from smib.common.utils import get_utc_datetime


class View(Model):
    view_id: str = Field[str](default=None)
    external_id: str = Field[str](default=None)
    last_modified: datetime = Field[datetime](default_factory=get_utc_datetime)
    view_json: dict = Field[dict](default={})

    @classmethod
    def retrieve(cls, /, view_id: str) -> Self:
        return View.find_one({"view_id": view_id})

    @classmethod
    def store(cls, /, view_id: str, view_json: dict, external_id: str):
        v = View.retrieve(view_id=view_id) or View()
        v.external_id = external_id
        v.view_id = view_id
        v.view_json = view_json
        v.last_modified = get_utc_datetime()
        v.save()

