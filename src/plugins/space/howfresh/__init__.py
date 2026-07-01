__display_name__ = "How Fresh?"
__description__ = "How fresh is the space?"
__author__ = "Sam Cork"

import logging
from typing import TYPE_CHECKING, TypedDict

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_sdk.models.blocks import Block, SectionBlock, MarkdownTextObject, DividerBlock
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.web.async_slack_response import AsyncSlackResponse

from smib.db.manager import DatabaseManager
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from smib.utilities import get_humanized_time
from .config import HOW_FRESH_PROFILE

if TYPE_CHECKING:
    from plugins.space.smibhid.sensor.models import SensorLog, SensorUnit

logger = logging.getLogger(__display_name__)

SUMMARY_MEASUREMENTS = ["temperature", "humidity", "light", "co2"]

SUMMARY_MEASUREMENT_ALIASES = {
    "relative_humidity": "humidity",
}

MEASUREMENT_NAME_FORMATS = {
    "co2": "CO₂",
}

MEASUREMENT_SYMBOLS = {
    "temperature": "🌡️",
    "humidity": "💧",
    "co2": "🌫️",
    "light": "💡",
    "pressure": "🧭",
}

MEASUREMENT_UNIT_FORMATS = {
    "c": "°C",
    "degc": "°C",
    "degrees c": "°C",
    "degrees celsius": "°C",
    "celsius": "°C",
    "percent": "%",
    "percentage": "%",
    "ppm": "ppm",
    "lux": "lux",
}


class SummaryReading(TypedDict):
    values: list[int | float]
    unit: str | None


def register(slack: AsyncApp, database: DatabaseManager, schedule: ScheduledEventInterface):
    async def how_fresh_loading(ack: AsyncAck, client: AsyncWebClient, command: dict, context: dict):
        await ack()

        full_command = get_full_command(command)
        command_mode = get_command_mode(command)

        logger.info(f"Received /howfresh command from user {command['user_name']} in channel {command['channel_name']}")
        logger.info(f"Full command: {full_command}")

        if command_mode not in {"", "detailed"}:
            logger.info(f"Unrecognized argument for /howfresh command: {command['text']}")
            await client.chat_postEphemeral(
                channel=command["channel_id"],
                user=command["user_id"],
                text="Usage: `/howfresh` or `/howfresh detailed`",
            )
            context["message_ts"] = None
            return

        context["howfresh_mode"] = command_mode

        resp: AsyncSlackResponse = await client.chat_postMessage(
            channel=command["channel_id"],
            text=get_loading_message(command_mode),
            **HOW_FRESH_PROFILE,
        )
        if not resp.status_code == 200:
            context["message_ts"] = None
            return

        context["message_ts"] = resp.data["ts"]

    async def how_fresh(client: AsyncWebClient, command: dict, context: dict):
        if not context.get("message_ts", None):
            return

        SensorLog = database.find_model_by_name("SensorLog")
        SensorUnit = database.find_model_by_name("SensorUnit")

        latest_log = await SensorLog.get_latest_log()
        if not latest_log:
            await update_message(
                client,
                command,
                context,
                text="No sensor readings found.",
            )
            logger.info("No sensor readings found")
            return

        logger.info(f"Latest sensor log: {get_sensor_data(latest_log)} at {latest_log.timestamp}")

        units_for_device = await SensorUnit.get_for_device(latest_log.device)
        if not units_for_device:
            await update_message(
                client,
                command,
                context,
                text="No sensor units found.",
            )
            logger.info(f"No sensor units found for device {latest_log.device}")
            return

        mode = context.get("howfresh_mode", get_command_mode(command))
        message_blocks = build_sensor_message_blocks(latest_log, units_for_device, detailed=mode == "detailed")

        await update_message(
            client,
            command,
            context,
            text="Sensor Readings!",
            blocks=message_blocks,
        )

    slack.command("/howfresh")(ack=how_fresh_loading, lazy=[how_fresh])


def get_command_mode(command: dict) -> str:
    return command.get("text", "").strip().lower()


def get_full_command(command: dict) -> str:
    return f"{command['command']} {command['text']}".strip()


def get_loading_message(mode: str) -> str:
    if mode == "detailed":
        return "Fetching detailed sensor readings..."

    return "Fetching sensor readings..."


async def update_message(
        client: AsyncWebClient,
        command: dict,
        context: dict,
        *,
        text: str,
        blocks: list[Block] | None = None,
):
    await client.chat_update(
        channel=command["channel_id"],
        ts=context["message_ts"],
        text=text,
        blocks=blocks,
        **HOW_FRESH_PROFILE,
    )


def build_sensor_message_blocks(sensor_log: "SensorLog", units: "SensorUnit", *, detailed: bool) -> list[Block]:
    if detailed:
        logger.info("Running detailed mode for /howfresh command")
        return build_detailed_sensor_message_blocks(sensor_log, units)

    logger.info("Running default mode for /howfresh command")
    return build_summary_sensor_message_blocks(sensor_log, units)


def build_message_header(sensor_log: "SensorLog", *, title: str = "Sensor Readings") -> list[Block]:
    return [
        SectionBlock(text=MarkdownTextObject(text=f"*{title} ({sensor_log.device}):*\n"
                                                  f"_Last updated {get_humanized_time(sensor_log.timestamp)}_")),
        DividerBlock(),
    ]


def get_sensor_data(sensor_log: "SensorLog") -> dict[str, dict[str, int | float]]:
    return sensor_log.data.model_dump()


def get_units_data(units: "SensorUnit") -> dict[str, dict[str, str]]:
    return units.sensors.model_dump()


def normalize_measurement_key(name: str) -> str:
    normalized_name = name.strip().lower()
    return SUMMARY_MEASUREMENT_ALIASES.get(normalized_name, normalized_name)


def normalize_measurement_name(name: str) -> str:
    normalized_name = normalize_measurement_key(name)

    if normalized_name in MEASUREMENT_NAME_FORMATS:
        return MEASUREMENT_NAME_FORMATS[normalized_name]

    return " ".join(word.capitalize() for word in normalized_name.split("_"))


def get_measurement_symbol(name: str) -> str:
    normalized_name = normalize_measurement_key(name)
    return MEASUREMENT_SYMBOLS.get(normalized_name, "•")


def normalize_measurement_unit(unit: str | None) -> str:
    if not unit:
        return ""

    normalized_unit = unit.strip().lower()
    return MEASUREMENT_UNIT_FORMATS.get(normalized_unit, unit)


def format_measurement_value(value: int | float) -> str:
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def format_measurement_with_unit(value: int | float, unit: str | None) -> str:
    formatted_value = format_measurement_value(value)
    formatted_unit = normalize_measurement_unit(unit)

    if not formatted_unit:
        return formatted_value

    return f"{formatted_value} {formatted_unit}"


def format_measurement_line(
        measurement_name: str,
        value: int | float,
        unit: str | None,
) -> str:
    symbol = get_measurement_symbol(measurement_name)
    display_name = normalize_measurement_name(measurement_name)
    formatted_measurement = format_measurement_with_unit(value, unit)

    return f"{symbol} *{display_name}*: {formatted_measurement}"


def build_detailed_sensor_message_blocks(sensor_log: "SensorLog", units: "SensorUnit") -> list[Block]:
    blocks = build_message_header(sensor_log)

    sensor_data = get_sensor_data(sensor_log)
    units_data = get_units_data(units)

    for sensor_name, readings in sensor_data.items():
        sensor_lines = [f"*{sensor_name}*"]
        sensor_units = units_data.get(sensor_name, {})

        for measurement_name, value in readings.items():
            unit = sensor_units.get(measurement_name)
            sensor_lines.append(format_measurement_line(measurement_name, value, unit))

        blocks.append(SectionBlock(text=MarkdownTextObject(text="\n".join(sensor_lines))))
        blocks.append(DividerBlock())

    remove_trailing_divider(blocks)

    return blocks


def build_summary_sensor_message_blocks(sensor_log: "SensorLog", units: "SensorUnit") -> list[Block]:
    blocks = build_message_header(sensor_log)

    summary_readings = collect_summary_readings(sensor_log, units)

    if not summary_readings:
        blocks.append(SectionBlock(text=MarkdownTextObject(text="No summary sensor readings found.")))
        return blocks

    summary_lines = [
        format_summary_measurement_line(measurement_name, summary_readings)
        for measurement_name in SUMMARY_MEASUREMENTS
        if normalize_measurement_key(measurement_name) in summary_readings
    ]

    blocks.append(SectionBlock(text=MarkdownTextObject(text="\n".join(summary_lines))))

    # Add instructions for how to get detailed readings
    blocks.append(DividerBlock())
    blocks.append(SectionBlock(text=MarkdownTextObject(text="_For detailed sensor readings, use `/howfresh detailed`._")))

    return blocks


def collect_summary_readings(sensor_log: "SensorLog", units: "SensorUnit") -> dict[str, SummaryReading]:
    sensor_data = get_sensor_data(sensor_log)
    units_data = get_units_data(units)

    summary_measurements = {
        normalize_measurement_key(measurement)
        for measurement in SUMMARY_MEASUREMENTS
    }

    summary_readings: dict[str, SummaryReading] = {}

    for sensor_name, readings in sensor_data.items():
        sensor_units = units_data.get(sensor_name, {})

        for measurement_name, value in readings.items():
            summary_measurement_name = normalize_measurement_key(measurement_name)

            if summary_measurement_name not in summary_measurements:
                continue

            if not isinstance(value, int | float):
                logger.debug(f"Skipping non-numeric summary measurement {sensor_name}.{measurement_name}: {value}")
                continue

            summary_reading = summary_readings.setdefault(
                summary_measurement_name,
                {
                    "values": [],
                    "unit": None,
                },
            )

            summary_reading["values"].append(value)

            unit = sensor_units.get(measurement_name)
            if unit and summary_reading["unit"] is None:
                summary_reading["unit"] = unit

    return summary_readings


def format_summary_measurement_line(
        measurement_name: str,
        summary_readings: dict[str, SummaryReading],
) -> str:
    summary_measurement_name = normalize_measurement_key(measurement_name)
    summary_reading = summary_readings[summary_measurement_name]

    values = summary_reading["values"]
    unit = summary_reading["unit"]

    average_value = sum(values) / len(values)

    return format_measurement_line(summary_measurement_name, average_value, unit)


def remove_trailing_divider(blocks: list[Block]) -> None:
    if blocks and isinstance(blocks[-1], DividerBlock):
        blocks.pop()