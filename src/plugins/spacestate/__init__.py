__display_name__ = "Space State"
__description__ = "A plugin to control the space state"
__author__ = "Sam Cork"

from http import HTTPStatus

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay

from smib.events.interfaces.http_event_interface import HttpEventInterface
from .config import SPACE_OPEN_ANNOUNCE_CHANNEL_ID
from .models import SpaceState, SpaceStateOpen, SpaceStateEnum


async def get_space_state_from_db() -> SpaceState:
    return await SpaceState.find_one() or SpaceState()

async def set_space_state_in_db(state: SpaceStateEnum) -> None:
    space_state = await get_space_state_from_db()
    space_state.open = state == SpaceStateEnum.OPEN
    await space_state.save()

async def send_space_open_announcement(say: AsyncSay, space_open_params: SpaceStateOpen) -> None:
    message = "Space Open!"
    if space_open_params.hours:
        message += f" (For about {space_open_params.hours}h)"

    await say(message, channel=SPACE_OPEN_ANNOUNCE_CHANNEL_ID)

async def send_space_closed_announcement(say: AsyncSay) -> None:
    await say("Space Closed!", channel=SPACE_OPEN_ANNOUNCE_CHANNEL_ID)


def register(slack: AsyncApp, http: HttpEventInterface):

    @http.put("/space/state/open", status_code=HTTPStatus.NO_CONTENT)
    async def set_space_open(say: AsyncSay, space_open_params: SpaceStateOpen) -> None:
        """ Set the space state to open """
        state: SpaceStateEnum = SpaceStateEnum.OPEN
        await set_space_state_in_db(state)
        await send_space_open_announcement(say, space_open_params)


    @http.put("/space/state/closed", status_code=HTTPStatus.NO_CONTENT)
    async def set_space_closed(say: AsyncSay) -> None:
        """ Set the space state to closed """
        state: SpaceStateEnum = SpaceStateEnum.CLOSED
        await set_space_state_in_db(state)
        await send_space_closed_announcement(say)


    @http.get("/space/state", response_model=SpaceState)
    async def get_space_state(say: AsyncSay):
        """ Get the space state """
        space_state = await get_space_state_from_db()
        return space_state


    @http.put("/smib/event/space_open", deprecated=True)
    async def set_space_open_from_smib_event(say: AsyncSay, space_open_params: SpaceStateOpen) -> None:
        """ Set the space state to open """
        state: SpaceStateEnum = SpaceStateEnum.OPEN
        await set_space_state_in_db(state)
        await send_space_open_announcement(say, space_open_params)

    @http.put("/smib/event/space_closed", deprecated=True)
    async def set_space_closed_from_smib_event(say: AsyncSay) -> None:
        """ Set the space state to closed """
        state: SpaceStateEnum = SpaceStateEnum.CLOSED
        await set_space_state_in_db(state)
        await send_space_closed_announcement(say)

    @http.get("/smib/event/space_state", deprecated=True)
    async def get_space_state_from_smib_event(say: AsyncSay):
        """ Get the space state """
        space_state = await get_space_state_from_db()
        return space_state
