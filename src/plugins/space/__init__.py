from typing import Literal

from beanie.odm.operators.update.general import Set
from pydantic import BaseModel
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay

from fastapi import Request, Response
from http import HTTPStatus

from smib.events.interfaces.http_event_interface import HttpEventInterface

from .models import SpaceState, SpaceStateDB


class State(BaseModel):
    state: Literal["open", "closed"]

def register(slack: AsyncApp, http: HttpEventInterface):

    @http.put("/space/state/{state}", status_code=HTTPStatus.NO_CONTENT)
    async def set_space_state(state: Literal["open", "closed"], say: AsyncSay) -> None:
        """ Set the space state to open or closed """
        await say(f"Space state changed to {state}", channel="#sam-test")
        space_open = state == "open"
        await SpaceStateDB.find_one().upsert(Set({ "open": space_open}),
                                             on_insert=SpaceStateDB(open=space_open))



    @http.get("/space/state", response_model=SpaceState)
    async def get_space_state(say: AsyncSay):
        space_state = await SpaceStateDB.find_one()
        return space_state

    @http.put("/smib/event/space_{state}")
    async def smib_event_space_open(state: Literal['open', 'closed'], say: AsyncSay):
        """ Deprecated endpoint for smib events """
        await set_space_state(state, say)
        return Response(status_code=HTTPStatus.NO_CONTENT)