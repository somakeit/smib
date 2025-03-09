__display_name__ = "Space State"
__description__ = "A plugin to control the space state"
__author__ = "sam57719"

from enum import StrEnum
from http import HTTPStatus
from typing import Literal, Annotated

from beanie.odm.operators.update.general import Set
from fastapi import Body
from pydantic import BaseModel
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay

from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.plugins.locator import PluginLocator
from .models import SpaceState, SpaceStateOpen

class SpaceStateEnum(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


async def get_space_state_from_db() -> SpaceState:
    return await SpaceState.find_one() or SpaceState()

async def set_space_state_in_db(state: SpaceStateEnum) -> None:
    space_state = await get_space_state_from_db()
    space_state.open = state == SpaceStateEnum.OPEN
    await space_state.save()


def register(slack: AsyncApp, http: HttpEventInterface):

    @http.put("/space/state/open", status_code=HTTPStatus.NO_CONTENT)
    async def set_space_open(say: AsyncSay, space_open_params: SpaceStateOpen) -> None:
        """ Set the space state to open or closed """
        state: SpaceStateEnum = SpaceStateEnum.OPEN
        await set_space_state_in_db(state)

        await say(f"Space state changed to {state}", channel="#sam-test")

    @http.put("/space/state/closed", status_code=HTTPStatus.NO_CONTENT)
    async def set_space_closed(say: AsyncSay) -> None:
        """ Set the space state to open or closed """
        state: SpaceStateEnum = SpaceStateEnum.CLOSED
        await set_space_state_in_db(state)

        await say(f"Space state changed to {state}", channel="#sam-test")


    @http.put("/smib/event/space_open", deprecated=True)
    async def set_space_open_from_smib_event(say: AsyncSay, space_open_params: SpaceStateOpen) -> None:
        """ Set the space state to open or closed """
        state: SpaceStateEnum = SpaceStateEnum.OPEN
        await set_space_state_in_db(state)

        await say(f"Space state changed to {state}", channel="#sam-test")

    @http.put("/smib/event/space_closed", deprecated=True)
    async def set_space_closed_from_smib_event(say: AsyncSay) -> None:
        """ Set the space state to open or closed """
        state: SpaceStateEnum = SpaceStateEnum.CLOSED
        await set_space_state_in_db(state)

        await say(f"Space state changed to {state}", channel="#sam-test")


    @http.get("/space/state", response_model=SpaceState)
    async def get_space_state(say: AsyncSay):
        """ Get the space state """
        space_state = await get_space_state_from_db()
        return space_state
