__plugin_name__ = "How Fresh?"
__description__ = "How fresh is the space?"
__author__ = "Sam Cork"

import json
import logging
from datetime import datetime, timedelta
from pprint import pformat
import requests
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from injectable import inject
from slack_bolt import Ack
from slack_sdk import WebClient
from slack_sdk.models.blocks import Block, ContextBlock, SectionBlock, MarkdownTextObject, DividerBlock
from slack_sdk.web import SlackResponse

from smib.slack.custom_app import CustomApp
from .config import HOW_FRESH_SMIBHID_HOST, HOW_FRESH_SMIBHID_BASE_URL

# Dependency Injection for CustomApp
app: CustomApp = inject("SlackApp")

# Global Variables
metadata: dict = {"sensors": {}}

HOW_FRESH_USERNAME = "How Fresh?"
HOW_FRESH_PICTURE = (
    "https://imgix.bustle.com/uploads/image/2018/5/11/8f6aebb3-90cc-4e5f-b153-96a21a765342-will-smith-fresh-prince-um-maluco-no-pedaco-netflix-xlarge_trans_nvbqzqnjv4bqnjjoebt78qiaydkjdey4cngtjfjs74myhny6w3gnbo8.jpg?w=350&h=350&fit=crop&crop=faces&dpr=2"
)

HOW_FRESH_PROFILE = {
    "username": HOW_FRESH_USERNAME,
    "icon_url": HOW_FRESH_PICTURE,
}

sensor_metadata_trigger = OrTrigger([
    DateTrigger(run_date=datetime.now() + timedelta(seconds=10)),
    IntervalTrigger(minutes=10)
])

logger = logging.getLogger(__plugin_name__)

# Helper Functions
def fetch_sensors() -> list[str]:
    """Fetch the list of sensors from the API."""
    try:
        resp = requests.get(f"{HOW_FRESH_SMIBHID_BASE_URL}/sensors/modules")
        if resp.ok:
            return resp.json()
    except Exception as e:
        logger.warning(f"Error fetching sensors: {e}")
    return []


def fetch_sensor_details(sensor: str) -> dict:
    """Fetch metadata details for a specific sensor."""
    try:
        resp = requests.get(f"{HOW_FRESH_SMIBHID_BASE_URL}/sensors/modules/{sensor}")
        if resp.ok:
            return resp.json()
        else:
            logger.warning(f"Failed to fetch details for sensor {sensor}: {resp.status_code}")
    except Exception as e:
        logger.warning(f"Error fetching sensor details for {sensor}: {e}")
    return {}


def update_sensor_metadata():
    """Update the global metadata dictionary with sensor data."""
    if not HOW_FRESH_SMIBHID_HOST:
        return

    sensors = fetch_sensors()
    for sensor in sensors:
        raw_data = fetch_sensor_details(sensor)
        if raw_data:
            # Reformulate the response as name: unit
            formatted_data = {
                entry["name"]: entry["unit"]
                for entry in raw_data
                if "name" in entry and "unit" in entry
            }
            metadata["sensors"][sensor] = formatted_data

    logger.info(pformat(metadata, sort_dicts=False))

def build_sensor_blocks(data: dict) -> list[Block]:
    """
    Build Slack message blocks containing sensor data.

    Args:
        data (dict): Sensor readings data.

    Returns:
        list[Block]: List of Slack message blocks.
    """
    blocks: list[Block] = [
        SectionBlock(text=MarkdownTextObject(text="*Sensor Readings:*")),
        DividerBlock(),
    ]

    if not metadata["sensors"]:
        logger.info("No sensor metadata found, updating...")
        update_sensor_metadata()
    elif not all(sensor in metadata['sensors'] for sensor in data):
        logger.info("Missing sensor metadata, updating...")
        update_sensor_metadata()

    for sensor_name, readings in data.items():
        units = metadata["sensors"].get(sensor_name, {})
        readable_data = "\n".join(
            [
                f"*{key.title()}:* {value} {units.get(key, '')}"
                for key, value in readings.items()
            ]
        )
        sensor_text = f"*{sensor_name}:*\n{readable_data}"
        blocks.append(SectionBlock(text=MarkdownTextObject(text=sensor_text)))
        blocks.append(DividerBlock())

    if len(blocks) > 2:  # Safely remove the last divider block
        blocks.pop()

    return blocks


# Scheduled Metadata Update Function
@app.schedule(sensor_metadata_trigger, id="how_fresh_metadata", name="How Fresh Metadata")
def how_fresh_metadata():
    """Scheduled task to update sensor metadata."""
    update_sensor_metadata()

def how_fresh_loading(ack: Ack, client: WebClient, command, context: dict):
    """ Acknowledge the command and send a loading message. """
    ack()
    if not HOW_FRESH_SMIBHID_HOST:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text="Unable to comply...\nHow Fresh SMIBHID host not configured...",
            **HOW_FRESH_PROFILE,
        )
        context['message_ts'] = None
        return

    resp: SlackResponse = client.chat_postMessage(
        channel=command["channel_id"],
        text="Fetching sensor readings...",
        **HOW_FRESH_PROFILE,
    )
    if not resp.status_code == 200:
        context['message_ts'] = None
        return

    context["message_ts"] = resp.data["ts"]


def how_fresh(ack, client: WebClient, command, context: dict,):
    """
    Handle the `/howfresh` Slack command to display sensor readings.
    """

    if not HOW_FRESH_SMIBHID_HOST:
        return

    if context.get('message_ts', None) is None:
        return
    data = {}

    try:
        # Fetch latest sensor readings
        resp = requests.get(f"{HOW_FRESH_SMIBHID_BASE_URL}/sensors/readings/latest")
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        client.chat_update(
            channel=command["channel_id"],
            ts=context['message_ts'],
            text=f"Unable to comply...\n{e}",
            **HOW_FRESH_PROFILE,
        )
        return

    # Build and send the Slack message
    message_blocks = build_sensor_blocks(data)
    client.chat_update(
        channel=command["channel_id"],
        text="Sensor Readings...",
        ts=context['message_ts'],
        blocks=[block.to_dict() for block in message_blocks],
        **HOW_FRESH_PROFILE,
    )

app.command("/howfresh")(ack=how_fresh_loading, lazy=[how_fresh])