__plugin_name__ = "Space Open/Close"
__description__ = "Space Open Close Button"
__author__ = "Sam Cork"

from injectable import inject

from smib.common.utils import http_bolt_response, is_json_encodable
from smib.slack.custom_app import CustomApp
from slack_sdk import WebClient
from slack_sdk.models.views import View
from slack_sdk.models.blocks import ActionsBlock, PlainTextObject, HeaderBlock, ButtonElement, SectionBlock, \
    MarkdownTextObject

from .models import Space

from smib.common.config import SPACE_OPEN_ANNOUNCE_CHANNEL_ID
from smib.slack.db import database

app: CustomApp = inject("SlackApp")


@database()
def get_app_home():
    blocks = []

    space = Space.single()

    # Header
    header_text = PlainTextObject(text="Welcome to S.M.I.B.", emoji=True)
    header_block = HeaderBlock(text=header_text)
    blocks.append(header_block)

    # State Text
    state_text = MarkdownTextObject(
        text=":warning: Unable to determine if So Make It is open or closed! :warning:" if space.open is None else
             f"So Make It is currently *{'open' if space.open else 'closed'}*!",
                                    )
    state_text_block = SectionBlock(text=state_text)
    blocks.append(state_text_block)

    # Buttons
    open_button = ButtonElement(
        text=PlainTextObject(text=":large_green_circle: Space Open", emoji=True),
        value="open",
        action_id="space_open",
        style="primary" if space.open is None or not space.open else None
    )

    closed_button = ButtonElement(
        text=PlainTextObject(text=":red_circle: Space Closed", emoji=True),
        value="closed",
        action_id="space_closed",
        style="danger" if space.open is None or space.open else None
    )

    # Action block with buttons
    action_block = ActionsBlock(elements=[open_button, closed_button])
    blocks.append(action_block)

    result = View(type="home", blocks=blocks)

    return result


@app.event('app_home_opened')
def app_home_opened(client: WebClient, event: dict):
    client.views_publish(user_id=event['user'], view=get_app_home())


@app.action('space_open')
@app.event('http_put_space_open')
@database()
def space_open(say, context, ack, client):
    ack()
    context['logger'].debug("Space Open!")
    say(text='Space Open!', channel=SPACE_OPEN_ANNOUNCE_CHANNEL_ID)

    space: Space = Space.single()
    space.set_open()

    # If we have a user_id, this means that this is from the app_home button
    user_id = context.get('user_id', None)
    if user_id is not None:
        client.views_publish(user_id=user_id, view=get_app_home())


@app.action('space_closed')
@app.event('http_put_space_closed')
@database()
def space_closed(say, context, ack, client):
    ack()
    context['logger'].debug("Space Closed!")

    say(text='Space Closed!', channel=SPACE_OPEN_ANNOUNCE_CHANNEL_ID)

    space: Space = Space.single()
    space.set_closed()

    # If we have a user_id, this means that this is from the app_home button
    user_id = context.get('user_id', None)
    if user_id is not None:
        client.views_publish(user_id=user_id, view=get_app_home())


@app.event("http_get_space_state")
@http_bolt_response
@database()
def get_space_state():
    space = Space.single()
    return {k: v for k, v in space.copy().items() if is_json_encodable(v)}
