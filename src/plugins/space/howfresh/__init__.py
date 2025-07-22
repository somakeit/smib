__display_name__ = "How Fresh?"
__description__ = "How fresh is the space?"
__author__ = "Sam Cork"

import logging
from typing import TYPE_CHECKING

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_sdk.models.blocks import Block, SectionBlock, MarkdownTextObject, DividerBlock
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.web.async_slack_response import AsyncSlackResponse

from smib.db.manager import DatabaseManager
from smib.utilities import get_humanized_time
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from .config import HOW_FRESH_PROFILE

if TYPE_CHECKING:
    from plugins.space.smibhid.sensor.models import SensorLog, SensorUnit

logger = logging.getLogger(__display_name__)

def register(slack: AsyncApp, database: DatabaseManager, schedule: ScheduledEventInterface):
    async def how_fresh_loading(ack: AsyncAck, client: AsyncWebClient, command: dict, context: dict):
        await ack()

        resp: AsyncSlackResponse = await client.chat_postMessage(
            channel=command["channel_id"],
            text="Fetching sensor readings...",
            **HOW_FRESH_PROFILE,
        )
        if not resp.status_code == 200:
            context['message_ts'] = None
            return

        context["message_ts"] = resp.data["ts"]

    async def how_fresh(client: AsyncWebClient, command: dict, context: dict):
        if not context.get("message_ts", None):
            return

        SensorLog = database.find_model_by_name("SensorLog")
        SensorUnit = database.find_model_by_name("SensorUnit")

        latest_log = await SensorLog.get_latest_log()
        if not latest_log:
            await client.chat_update(
                channel=command["channel_id"],
                ts=context["message_ts"],
                text="No sensor readings found.",
                **HOW_FRESH_PROFILE,
            )
            return

        units_for_device = await SensorUnit.get_for_device(latest_log.device)
        if not units_for_device:
            await client.chat_update(
                channel=command["channel_id"],
                ts=context["message_ts"],
                text="No sensor units found.",
                **HOW_FRESH_PROFILE,
            )
            return

        message_blocks = build_sensor_message_blocks(latest_log, units_for_device)

        await client.chat_update(
            channel=command["channel_id"],
            ts=context["message_ts"],
            blocks=message_blocks,
            text="Sensor Readings!"
        )

    slack.command("/howfresh")(ack=how_fresh_loading, lazy=[how_fresh])

def normalize_measurement_name(name: str) -> str:

    special_cases = {
        'co2': 'CO2',
    }

    if name.lower() in special_cases:
        return special_cases[name.lower()]

    return ' '.join(word.capitalize() for word in name.split('_'))

def build_sensor_message_blocks(sensor_log: "SensorLog", units: "SensorUnit") -> list[Block]:
    blocks: list[Block] = [
        SectionBlock(text=MarkdownTextObject(text=f"*Sensor Readings ({sensor_log.device}):*\n"
                                                  f"_Last updated {get_humanized_time(sensor_log.timestamp)}_")),
        DividerBlock(),
    ]

    sensor_data = sensor_log.data.model_dump()
    units_data = units.sensors.model_dump()

    for sensor_name, readings in sensor_data.items():
        sensor_text = f"*{sensor_name}*\n"
        readings_dict = readings

        for measurement, value in readings_dict.items():
            unit = units_data[sensor_name][measurement]
            # Format float values to 2 decimal places
            formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
            sensor_text += f"• {normalize_measurement_name(measurement)}: {formatted_value} {unit}\n"

        blocks.append(SectionBlock(text=MarkdownTextObject(text=sensor_text)))
        blocks.append(DividerBlock())

    # Remove the last divider block for cleaner look
    blocks.pop()

    return blocks


