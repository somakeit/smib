__display_name__ = "Space State"
__description__ = "A plugin to control the space state"
__author__ = "sam57719"

from http import HTTPStatus
from typing import Literal, Annotated

from beanie.odm.operators.update.general import Set
from fastapi import Body
from pydantic import BaseModel
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay

from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.plugins.locator import PluginLocator
from .models import SpaceState, StateSetExtras


async def get_space_state_from_db() -> SpaceState:
    return await SpaceState.find_one() or SpaceState()


def register(slack: AsyncApp, http: HttpEventInterface):
    @http.put("/space/state/{state}", status_code=HTTPStatus.NO_CONTENT)
    @http.put("/smib/event/space_{state}", deprecated=True)
    async def set_space_state(
            say: AsyncSay,
            state: Literal["open", "closed"],
            state_extras: StateSetExtras = Body(default_factory=StateSetExtras)
    ) -> None:
        """ Set the space state to open or closed """
        await say(f"Space state changed to {state}", channel="#sam-test")

        space_state = await get_space_state_from_db()
        space_state.open = state == "open"

        print(state_extras)

        await space_state.save()

    @http.get("/space/state", response_model=SpaceState)
    async def get_space_state(say: AsyncSay):
        """ Get the space state """
        space_state = await get_space_state_from_db()
        return space_state

    1/0
