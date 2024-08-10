from pydantic import BaseModel
from typing import Literal


class ButtonPressEvent(BaseModel):
    button_name: str
    button_id: str


class UILog(BaseModel):
    event: ButtonPressEvent
    type: Literal['button_press', 'rotary_dial']
    timestamp: int


class UILogs(BaseModel):
    ui_logs: list[UILog]

    def __iter__(self):
        yield from self.ui_logs



