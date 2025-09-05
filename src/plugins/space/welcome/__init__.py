__display_name__ = "Welcome"
__description__ = "Welcomes new users"

import json
import re
from functools import lru_cache
from pathlib import Path

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay

from smib.events.interfaces.http_event_interface import HttpEventInterface


@lru_cache
def get_welcome_message_blocks() -> dict:
    with (Path(__file__).parent / "welcome.json").open("r", encoding="utf-8") as f:
        return json.load(f)

def register(slack: AsyncApp, http: HttpEventInterface):
    @slack.event("team_join")
    async def welcome(event: dict, say: AsyncSay):
        await say(blocks=get_welcome_message_blocks(), channel=event["user"]["id"])

    @slack.action(re.compile('welcome_message_url_.*'))
    async def handle_welcome_message_url_clicks(ack: AsyncAck):
        await ack()




