import logging
import re

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay
from slack_sdk.web.async_client import AsyncWebClient

from ..app_home import get_app_home, extract_selected_hours_from_state, extract_selected_minutes_from_state
from ..common import open_space, \
    close_space
from ..models import SpaceStateOpen, SpaceStateClosed

logger = logging.getLogger("Space State Plugin - Slack")

def register(slack: AsyncApp):
    @slack.event("app_home_opened")
    async def handle_app_home_opened_events(event: dict, client: AsyncWebClient):
        await client.views_publish(user_id=event["user"], view=await get_app_home())

    @slack.action("space_open_button")
    async def handle_space_open_button_clicks(ack: AsyncAck, body: dict, context: dict, client: AsyncWebClient, say: AsyncSay):
        await ack()

        params = SpaceStateOpen(hours=extract_selected_hours_from_state(body['view']['state']))

        logger.info(f"Space Open Button clicked by {body['user']['name']} ({body['user']['id']}) with {params.hours}h selected.")

        await open_space(params, say)
        await client.views_publish(user_id=context['user_id'], view=await get_app_home())

    @slack.action("space_closed_button")
    async def handle_space_close_button_clicks(ack: AsyncAck, body: dict, context: dict, client: AsyncWebClient, say: AsyncSay):
        await ack()

        params = SpaceStateClosed(minutes=extract_selected_minutes_from_state(body['view']['state']))

        logger.info(f"Space Closed Button clicked by {body['user']['name']} ({body['user']['id']})")

        await close_space(params, say)
        await client.views_publish(user_id=context['user_id'], view=await get_app_home())

    @slack.action("space_open_hours_select")
    async def handle_space_open_hours_select(ack: AsyncAck):
        await ack()

    @slack.action("space_closed_minutes_select")
    async def handle_space_open_hours_select(ack: AsyncAck):
        await ack()

    @slack.action(re.compile('app_home_url_.*'))
    async def handle_app_home_url_clicks(ack: AsyncAck):
        await ack()