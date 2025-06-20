from http import HTTPStatus

from slack_bolt.context.say.async_say import AsyncSay

from smib.events.interfaces.http_event_interface import HttpEventInterface
from ..common import set_space_state_in_db, send_space_open_announcement, send_space_closed_announcement, \
    get_space_state_from_db, open_space, close_space
from ..models import SpaceState, SpaceStateEnum, SpaceStateOpen


def register(http: HttpEventInterface):

    @http.put("/space/state/open", status_code=HTTPStatus.NO_CONTENT)
    async def set_space_open(say: AsyncSay, space_open_params: SpaceStateOpen) -> None:
        """ Set the space state to open """
        await open_space(space_open_params, say)


    @http.put("/space/state/closed", status_code=HTTPStatus.NO_CONTENT)
    async def set_space_closed(say: AsyncSay) -> None:
        """ Set the space state to closed """
        await close_space(say)


    @http.get("/space/state", response_model=SpaceState)
    async def get_space_state():
        """ Get the space state """
        space_state = await get_space_state_from_db()
        return space_state


    @http.put("/smib/event/space_open", deprecated=True)
    async def set_space_open_from_smib_event(say: AsyncSay, space_open_params: SpaceStateOpen) -> None:
        """ Set the space state to open """
        await open_space(space_open_params, say)

    @http.put("/smib/event/space_closed", deprecated=True)
    async def set_space_closed_from_smib_event(say: AsyncSay) -> None:
        """ Set the space state to closed """
        await close_space(say)

    @http.get("/smib/event/space_state", deprecated=True)
    async def get_space_state_from_smib_event(say: AsyncSay):
        """ Get the space state """
        space_state = await get_space_state_from_db()
        return space_state