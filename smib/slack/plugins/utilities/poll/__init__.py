__plugin_name__ = "SMIB Poll"
__description__ = "Create and track polls"
__author__ = "Sam Cork"

import json
import re
from logging import Logger
from pathlib import Path
from pprint import pformat

from injectable import inject
from slack_sdk.models.blocks import InputBlock, PlainTextInputElement, ActionsBlock, DividerBlock
from slack_sdk.models.blocks.block_elements import ConversationSelectElement, ButtonElement
from slack_sdk.models.views import View
from slack_sdk.web import SlackResponse

from .views import PollView
from smib.slack.custom_app import CustomApp
from slack_sdk.web.client import WebClient

app: CustomApp = inject("SlackApp")


@app.global_shortcut('smib-poll')
def smib_poll_shortcut(body, payload, ack, client: WebClient, context: dict):
    ack()
    logger: Logger = context.get("logger")

    view = PollView(type="modal", title="Create Poll", submit="Create", external_id="create_poll")
    blocks = [
        InputBlock(label="Title", block_id="poll_title", element=PlainTextInputElement()),
        InputBlock(block_id="poll_option_1", label="Option 1", element=PlainTextInputElement()),
        InputBlock(block_id="poll_option_2", label="Option 2", element=PlainTextInputElement()),
        ActionsBlock(block_id="options_actions", elements=[
            ButtonElement(text="Add another option", action_id="add_option", style="primary"),
            ButtonElement(text="Remove option", action_id="remove_option", style="danger"),
        ]),
        DividerBlock(),
        InputBlock(block_id="channel_select", label="Select a channel",
                   element=ConversationSelectElement(placeholder="Select a channel")),
    ]
    view.blocks = blocks

    print(view.to_dict())

    resp: SlackResponse | None = None
    try:
        resp: SlackResponse = client.views_open(
            trigger_id=payload["trigger_id"],
            view=view
        )
    except Exception as e:
        logger.exception(e)


@app.block_action("add_option")
def add_option(ack, payload: dict, context: dict):
    ack()

    logger: Logger = context.get("logger")
    logger.debug(pformat(payload))


@app.block_action("remove_option")
def remove_option(ack, payload: dict, context: dict):
    ack()

    logger: Logger = context.get("logger")
    logger.debug(pformat(payload))
