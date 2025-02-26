import inspect
from typing import Literal

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay

from smib.events.interfaces.http_event_interface import HttpEventInterface


def register(slack: AsyncApp, http: HttpEventInterface):

    @http.put("/space/{state}")
    async def space(state: Literal["open", "closed"], say: AsyncSay):
        """ Set the space state to open or closed """
        await say(f"Space state changed to {state}", channel="#general")
        return {
            "state": state,
        }
