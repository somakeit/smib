import logging

from slack_bolt.context.say.async_say import AsyncSay

from .config import SPACE_OPEN_ANNOUNCE_CHANNEL_ID
from .models import SpaceState, SpaceStateOpen, SpaceStateEnum, SpaceStateHistory

logger = logging.getLogger("Space State Plugin - Common")

async def get_space_state_from_db() -> SpaceState:
    return await SpaceState.find_one() or SpaceState()

async def set_space_state_in_db(state: SpaceStateEnum) -> None:
    logger.debug(f"Setting space state to {state} in DB")
    space_state = await get_space_state_from_db()
    space_state.open = state == SpaceStateEnum.OPEN
    await space_state.save()

async def get_space_state_enum_from_db() -> SpaceStateEnum | None:
    state = await get_space_state_from_db()
    return SpaceStateEnum.OPEN if state.open else None if state.open is None else SpaceStateEnum.CLOSED

async def log_to_space_state_history(state: SpaceStateEnum) -> None:
    await SpaceStateHistory(open=state == SpaceStateEnum.OPEN).save()

async def send_space_open_announcement(say: AsyncSay, space_open_params: SpaceStateOpen) -> None:
    message = "Space Open!"
    if space_open_params.hours:
        message += f" (For about {space_open_params.hours}h)"

    await say(message, channel=SPACE_OPEN_ANNOUNCE_CHANNEL_ID)

async def send_space_closed_announcement(say: AsyncSay) -> None:
    await say("Space Closed!", channel=SPACE_OPEN_ANNOUNCE_CHANNEL_ID)

async def open_space(space_open_params: SpaceStateOpen, say: AsyncSay) -> None:
    new_state: SpaceStateEnum = SpaceStateEnum.OPEN
    old_state: SpaceStateEnum = await get_space_state_enum_from_db()

    # Only update the DB if the state has changed
    if old_state is not new_state:
        await set_space_state_in_db(new_state)
        await log_to_space_state_history(new_state)

    await send_space_open_announcement(say, space_open_params)

async def close_space(say: AsyncSay) -> None:
    new_state: SpaceStateEnum = SpaceStateEnum.CLOSED
    old_state: SpaceStateEnum = await get_space_state_enum_from_db()

    # Only update the DB if the state has changed
    if old_state is not new_state:
        await set_space_state_in_db(new_state)
        await log_to_space_state_history(new_state)

    await send_space_closed_announcement(say)