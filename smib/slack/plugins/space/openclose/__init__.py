__plugin_name__ = "Space Open/Close"
__description__ = "Space Open Close Button"
__author__ = "Sam Cork"

from injectable import inject

from smib.common.utils import http_bolt_response
from smib.slack.custom_app import CustomApp
from slack_sdk import WebClient
from slack_sdk.models.views import View
from slack_sdk.models.blocks import ActionsBlock, PlainTextObject, HeaderBlock, ButtonElement

from .models import Space

from smib.common.config import SPACE_OPEN_ANNOUNCE_CHANNEL_ID
from smib.slack.db import database

app: CustomApp = inject("SlackApp")


def get_app_home():
    header_text = PlainTextObject(text="Welcome to S.M.I.B.", emoji=True)
    header_block = HeaderBlock(text=header_text)

    # Buttons
    open_button = ButtonElement(
        text=PlainTextObject(text="Space Open", emoji=True),
        value="open",
        action_id="space_open"
    )

    closed_button = ButtonElement(
        text=PlainTextObject(text="Space Closed", emoji=True),
        value="closed",
        action_id="space_closed"
    )

    # Action block with buttons
    action_block = ActionsBlock(elements=[open_button, closed_button])

    result = View(type="home", blocks=[header_block, action_block])

    return result


@app.event('app_home_opened')
def app_home_opened(client: WebClient, event: dict):
    client.views_publish(user_id=event['user'], view=get_app_home())


@app.action('space_open')
@app.event('http_put_space_open')
@database()
def space_open(say, context, ack):

    ack()
    context['logger'].debug("Space Open!")
    say(text='Space Open!', channel=SPACE_OPEN_ANNOUNCE_CHANNEL_ID)

    space: Space = Space.single()
    space.set_open()


@app.action('space_closed')
@app.event('http_put_space_closed')
@database()
def space_closed(say, context, ack):

    ack()
    context['logger'].debug("Space Closed!")

    say(text='Space Closed!', channel=SPACE_OPEN_ANNOUNCE_CHANNEL_ID)

    space: Space = Space.single()
    space.set_closed()


@app.event("http_get_space_state")
@http_bolt_response
@database()
def get_space_state():
    space = Space.single()
    return {
        "open": space.open
    }
