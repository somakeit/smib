import logging
from http import HTTPStatus
from typing import Annotated
from fastapi import Request, Body
from slack_bolt.context.say.async_say import AsyncSay

from smib.events.interfaces.http_event_interface import HttpEventInterface
from ..common import set_space_state_in_db, send_space_open_announcement, send_space_closed_announcement, \
    get_space_state_from_db, open_space, close_space
from ..models import SpaceState, SpaceStateEnum, SpaceStateOpen, SpaceStateClosed

logger = logging.getLogger("Space State Plugin - HTTP")

def register(http: HttpEventInterface):

    @http.put("/space/state/open", status_code=HTTPStatus.NO_CONTENT)
    async def set_space_open(
        say: AsyncSay, 
        space_open_params: Annotated[SpaceStateOpen | None, Body()] = None
    ) -> None:
        """ Set the space state to open """
        space_open_params = space_open_params or SpaceStateOpen()
        logger.info(f"Received space open request with {space_open_params.hours}h selected.")
        await open_space(space_open_params, say)

    @http.put("/space/state/closed", status_code=HTTPStatus.NO_CONTENT)
    async def set_space_closed(
        say: AsyncSay, 
        space_closed_params: Annotated[SpaceStateClosed | None, Body()] = None
    ) -> None:
        """ Set the space state to closed """
        space_closed_params = space_closed_params or SpaceStateClosed()
        logger.info(f"Received space closed request with {space_closed_params.minutes}m selected.")
        await close_space(space_closed_params, say)


    @http.get("/space/state", response_model=SpaceState)
    async def get_space_state() -> SpaceState:
        """ Get the space state """
        logger.info("Received space state request.")
        space_state = await get_space_state_from_db()
        logger.info(f"Returning space state: {SpaceStateEnum.OPEN if space_state.open else None if space_state.open is None else SpaceStateEnum.CLOSED}")
        return space_state


    @http.put("/smib/event/space_open", deprecated=True)
    async def set_space_open_from_smib_event(
        say: AsyncSay, 
        space_open_params: Annotated[SpaceStateOpen | None, Body()] = None
    ) -> None:
        """ Set the space state to open """
        space_open_params = space_open_params or SpaceStateOpen()
        logger.info(f"Received legacy space open request (deprecated) with {space_open_params.hours}h selected.")
        await open_space(space_open_params, say)

    @http.put("/smib/event/space_closed", deprecated=True)
    async def set_space_closed_from_smib_event(
        say: AsyncSay, 
        space_closed_params: Annotated[SpaceStateClosed | None, Body()] = None
    ) -> None:
        """ Set the space state to closed """
        space_closed_params = space_closed_params or SpaceStateClosed()
        logger.info("Received legacy space closed request (deprecated).")
        await close_space(space_closed_params, say)

    @http.get("/smib/event/space_state", deprecated=True)
    async def get_space_state_from_smib_event(say: AsyncSay) -> SpaceState:
        """ Get the space state """
        logger.info("Received legacy space state request (deprecated).")
        space_state = await get_space_state_from_db()
        logger.info(f"Returning space state: {SpaceStateEnum.OPEN if space_state.open else None if space_state.open is None else SpaceStateEnum.CLOSED}")
        return space_state