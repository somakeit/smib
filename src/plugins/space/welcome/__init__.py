__display_name__ = "Welcome"
__description__ = "Welcomes new users"

import json
import re
from functools import lru_cache
from pathlib import Path
from pprint import pprint

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay


@lru_cache
def get_welcome_message_blocks() -> dict:
    with (Path(__file__).parent / "welcome.json").open("r", encoding="utf-8") as f:
        return json.load(f)

async def send_welcome_message(say: AsyncSay, user: str) -> None:
    await say(blocks=get_welcome_message_blocks(), channel=user, text="Welcome to SoMakeIt!")


def register(slack: AsyncApp):
    @slack.event("team_join")
    async def welcome(event: dict, say: AsyncSay, ack: AsyncAck):
        await ack()
        pprint(event)
        await send_welcome_message(say, event["user"]["id"])

    @slack.command('/welcome')
    async def welcome_command(ack: AsyncAck, say: AsyncSay, command: dict, client):
        await ack()
        await client.chat_postEphemeral(channel=command["channel_id"], user=command["user_id"], text="Check messages from @SMIB...")
        await send_welcome_message(say, command["user_id"])

    @slack.action(re.compile('welcome_message_url_.*'))
    async def handle_welcome_message_url_clicks(ack: AsyncAck):
        await ack()




