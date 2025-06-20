from slack_bolt.context.say.async_say import AsyncSay

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

async def open_space(space_open_params: SpaceStateOpen, say: AsyncSay) -> None:
    state: SpaceStateEnum = SpaceStateEnum.OPEN
    await set_space_state_in_db(state)
    await send_space_open_announcement(say, space_open_params)

async def close_space(say: AsyncSay) -> None:
    state: SpaceStateEnum = SpaceStateEnum.CLOSED
    await set_space_state_in_db(state)
    await send_space_closed_announcement(say)
