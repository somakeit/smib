__display_name__ = "Lazy Listener Test"
__description__ = "Plugin to test Lazy Listeners"

import asyncio
import random

from slack_bolt.context.say.async_say import AsyncSay

from smib.events.interfaces.http_event_interface import HttpEventInterface


def register(http: HttpEventInterface):
    async def lazy_response() -> dict:
        return {"lazy": True}

    async def lazy_1(say: AsyncSay):
        delay = random.randint(1, 5)
        await asyncio.sleep(delay)
        await say(f"Lazyyy after {delay}s", channel="sam-test")

    http.get('/lazy')(ack=lazy_response, lazy=[lazy_1])

