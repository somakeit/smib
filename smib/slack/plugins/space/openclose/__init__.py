__plugin_name__ = "Space Open/Close"
__description__ = "Space Open Close Button"
__author__ = "Sam Cork"

import re
from logging import Logger
from pprint import pformat

from injectable import inject
from slack_sdk.errors import SlackApiError

from smib.common.utils import http_bolt_response, is_json_encodable
from smib.slack.custom_app import CustomApp
from slack_sdk import WebClient
from .app_home import get_app_home

from .models import Space

from .config import SPACE_OPEN_ANNOUNCE_CHANNEL_ID
from smib.slack.db import database

app: CustomApp = inject("SlackApp")


@app.event('app_home_opened')
def app_home_opened(client: WebClient, event: dict):
    client.views_publish(user_id=event['user'], view=get_app_home())


# Still need to acknowledge url button presses
app.action(re.compile('app_home_url_.*'))(lambda ack: ack())


@app.action('space_open')
@app.event('http_put_space_open')
@database()
def space_open(say, context, ack, client, event, action):
    ack()
    logger: Logger = context.get('logger')

    request_data: dict = {}

    if event:
        logger.info(f"Processing event: {event['type']}")
        request_data = event.get('data', {})
    elif action:
        logger.info(f"Processing action: {action['action_id']}")

    logger.debug(pformat(request_data, sort_dicts=False))
    logger.debug("Space Open!")

    hours_open = request_data.get('hours', 0)

    try:
        if hours_open:
            say(text=f'Space Open! (For about {hours_open}h)', channel=SPACE_OPEN_ANNOUNCE_CHANNEL_ID)
        else:
            say(text='Space Open!', channel=SPACE_OPEN_ANNOUNCE_CHANNEL_ID)

    except SlackApiError as e:
        logger.debug(f"{SPACE_OPEN_ANNOUNCE_CHANNEL_ID = }")
        logger.warning(e)

    space: Space = Space.single()
    space.set_open()

    # If we have a user_id, this means that this is from the app_home button
    user_id = context.get('user_id', None)
    if user_id is not None:
        client.views_publish(user_id=user_id, view=get_app_home())


@app.action('space_closed')
@app.event('http_put_space_closed')
@database()
def space_closed(say, context, ack, client, event, action):
    ack()
    logger: Logger = context.get('logger')

    request_data: dict = {}

    if event:
        logger.info(f"Processing event: {event['type']}")
        request_data = event.get('data', {})
    elif action:
        logger.info(f"Processing action: {action['action_id']}")

    logger.debug(pformat(request_data, sort_dicts=False))
    logger.debug("Space Closed!")

    try:
        say(text='Space Closed!', channel=SPACE_OPEN_ANNOUNCE_CHANNEL_ID)
    except SlackApiError as e:
        logger.debug(f"{SPACE_OPEN_ANNOUNCE_CHANNEL_ID = }")
        logger.warning(e)

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
