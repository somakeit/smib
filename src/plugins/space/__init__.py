from typing import Literal

from pydantic import BaseModel
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay

from fastapi import Request, Response
from http import HTTPStatus

from smib.events.interfaces.http_event_interface import HttpEventInterface

class SpaceState(BaseModel):
    open: bool

class State(BaseModel):
    state: Literal["open", "closed"]

def register(slack: AsyncApp, http: HttpEventInterface):

    @http.put("/space/state/{state}", status_code=HTTPStatus.NO_CONTENT)
    async def space(state: Literal["open", "closed"], say: AsyncSay) -> None:
        """ Set the space state to open or closed """
        await say(f"Space state changed to {state}", channel="#general")

    @http.get("/space/state", response_model=SpaceState)
    async def space(say: AsyncSay):
        return {
            "open": True
        }