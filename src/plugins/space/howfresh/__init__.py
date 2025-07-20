__display_name__ = "How Fresh?"
__description__ = "How fresh is something?"
__author__ = "Sam Cork"

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_sdk.web.async_client import AsyncWebClient

from plugins.space.smibhid.sensor.models import SensorLog
from .config import HOW_FRESH_PROFILE

def register(slack: AsyncApp):
    @slack.command("/howfresh")
    async def how_fresh(ack: AsyncAck, client: AsyncWebClient, command):
        await ack()
        sensor_log: SensorLog = await get_latest_sensor_log_from_db()
        await client.chat_postMessage(
            channel=command["channel_id"],
            text="Fetching sensor readings...",
            **HOW_FRESH_PROFILE,
        )


async def get_latest_sensor_log_from_db() -> SensorLog:
    return await SensorLog.find_one({}, sort=[("timestamp", -1)])



