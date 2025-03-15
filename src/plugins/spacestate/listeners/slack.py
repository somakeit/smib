import re

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay
from slack_sdk.web.async_client import AsyncWebClient

from ..app_home import get_app_home, extract_selected_hours_from_state
from ..common import set_space_state_in_db, send_space_open_announcement, send_space_closed_announcement
from ..models import SpaceStateEnum, SpaceStateOpen


def register(slack: AsyncApp):
    @slack.event("app_home_opened")
    async def handle_app_home_opened_events(event: dict, client: AsyncWebClient, logger):
        await client.views_publish(user_id=event["user"], view=await get_app_home())

    @slack.action("space_open_button")
    async def handle_space_open_button_clicks(ack: AsyncAck, body: dict, context: dict, client: AsyncWebClient, say: AsyncSay):
        await ack()
        await set_space_state_in_db(SpaceStateEnum.OPEN)

        params = SpaceStateOpen(hours=extract_selected_hours_from_state(body['view']['state']))
        await send_space_open_announcement(say, params)

        await client.views_publish(user_id=context['user_id'], view=await get_app_home())

    @slack.action("space_closed_button")
    async def handle_space_close_button_clicks(ack: AsyncAck, body: dict, context: dict, client: AsyncWebClient, say: AsyncSay):
        await ack()
        await set_space_state_in_db(SpaceStateEnum.CLOSED)

        await send_space_closed_announcement(say)

        await client.views_publish(user_id=context['user_id'], view=await get_app_home())

    @slack.action("space_open_hours_select")
    async def handle_space_open_hours_select(ack: AsyncAck):
        await ack()

    @slack.action(re.compile('app_home_url_.*'))
    async def handle_app_home_url_clicks(ack: AsyncAck):
        await ack()