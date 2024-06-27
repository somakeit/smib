import json
from typing import Self

from slack_sdk.models.views import View
from os import PathLike


class Modal(View):
    def __init__(self, /, **kwargs):
        kwargs['type'] = "modal"
        super().__init__(**kwargs)

    @classmethod
    def from_dict(cls, json_dict: dict) -> Self:
        return cls(**json_dict)

    @classmethod
    def from_file(cls, file_path: PathLike) -> Self:
        return cls(**json.load(open(file_path)))


