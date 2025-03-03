__display_name__ = "Space State"
__description__ = "A plugin to control the space state"
__author__ = "sam57719"

from http import HTTPStatus
from typing import Literal

from beanie.odm.operators.update.general import Set
from pydantic import BaseModel
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay

from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.plugins.locator import PluginLocator
from .models import SpaceState

def register(slack: AsyncApp, http: HttpEventInterface):

    @http.put("/space/state/{state}", status_code=HTTPStatus.NO_CONTENT)
    @http.put("/smib/event/space_{state}", deprecated=True)
    async def set_space_state(state: Literal["open", "closed"], say: AsyncSay) -> None:
        """ Set the space state to open or closed """
        await say(f"Space state changed to {state}", channel="#sam-test")
        space_open = state == "open"
        await SpaceState.find_one().upsert(Set({ "open": space_open}),
                                             on_insert=SpaceState(open=space_open))

    @http.get("/space/state", response_model=SpaceState)
    async def get_space_state(say: AsyncSay):
        space_state = await SpaceState.find_one()
        return space_state