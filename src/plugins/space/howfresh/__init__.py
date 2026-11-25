__display_name__ = "How Fresh?"
__description__ = "How fresh is the space?"
__author__ = "Sam Cork"

import logging
from datetime import UTC, datetime, timedelta
from typing import Callable, TYPE_CHECKING, TypedDict

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_sdk.models.blocks import (
    Block,
    ContextBlock,
    DividerBlock,
    MarkdownTextObject,
    RawTextObject,
    RichTextBlock,
    RichTextElementParts,
    RichTextSectionElement,
    SectionBlock,
    TableBlock,
    TableBlockColumnSettings,
)
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.web.async_slack_response import AsyncSlackResponse

from smib.db.manager import DatabaseManager
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from smib.utilities import get_humanized_time, get_humanized_timedelta
from .config import HOW_FRESH_PROFILE
from ..smibhid.config import config as device_config

if TYPE_CHECKING:
    from plugins.space.smibhid.sensor.models import SensorLog, SensorUnit

logger = logging.getLogger(__display_name__)

SUMMARY_MEASUREMENTS = ["temperature", "humidity", "light", "co2"]

SENSOR_ORDER = ["BH1750", "BME280", "SCD30", "PMSA003I", "InternalMetrics"]

SUMMARY_MEASUREMENT_ALIASES = {
    "relative_humidity": "humidity",
}

MEASUREMENT_ORDER = [
    "temperature",
    "humidity",
    "relative_humidity",
    "pressure",
    "light",
    "co2",
    "pm10_standard",
    "pm25_standard",
    "pm100_standard",
    "pm10_env",
    "pm25_env",
    "pm100_env",
    "particles_03um",
    "particles_05um",
    "particles_10um",
    "particles_25um",
    "particles_50um",
    "particles_100um",
    "relay_on_time",
]

SENSOR_SORT_ORDER = {name: index for index, name in enumerate(SENSOR_ORDER)}
MEASUREMENT_SORT_ORDER = {name: index for index, name in enumerate(MEASUREMENT_ORDER)}

MEASUREMENT_NAME_FORMATS = {
    "temperature": "Temperature",
    "humidity": "Humidity",
    "relative_humidity": "Relative Humidity",
    "pressure": "Pressure",
    "light": "Light",
    "co2": "CO₂",

    "pm10_standard": "PM1.0 (Standard)",
    "pm25_standard": "PM2.5 (Standard)",
    "pm100_standard": "PM10 (Standard)",
    "pm10_env": "PM1.0 (Environmental)",
    "pm25_env": "PM2.5 (Environmental)",
    "pm100_env": "PM10 (Environmental)",

    "particles_03um": "Particles ≥0.3 μm",
    "particles_05um": "Particles ≥0.5 μm",
    "particles_10um": "Particles ≥1.0 μm",
    "particles_25um": "Particles ≥2.5 μm",
    "particles_50um": "Particles ≥5.0 μm",
    "particles_100um": "Particles ≥10.0 μm",

    "relay_on_time": "Relay On Time",
}

MEASUREMENT_SYMBOLS = {
    "temperature": "🌡️",
    "humidity": "💧",
    "co2": "🌫️",
    "light": "💡",
    "pressure": "🧭",

    "pm25_standard": "🌫️",
    "pm10_standard": "🌫️",
    "pm100_standard": "🌫️",

    "pm25_env": "🌫️",
    "pm10_env": "🌫️",
    "pm100_env": "🌫️",

    "particles_03um": "🫧",
    "particles_05um": "🫧",
    "particles_10um": "🫧",
    "particles_25um": "🫧",
    "particles_50um": "🫧",
    "particles_100um": "🫧",

    "relay_on_time": "🔌",
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
    "ug/m3": "μg/m³",
}

SENSOR_NAME_FORMATS = {
    "BH1750": "Light (BH1750)",
    "BME280": "Climate (BME280)",
    "SCD30": "Air Quality (SCD30)",
    "PMSA003I": "Particles (PMSA003I)",
    "InternalMetrics": "Internal Metrics",
}

# --- Measurement value formatting ---
#
# Some measurements need bespoke formatting beyond a plain numeric value
# plus unit (e.g. a duration in seconds should read as human time rather
# than a raw number). Register those here, keyed by the normalized
# measurement name; anything not listed falls back to
# `format_measurement_with_unit`.

MEASUREMENT_VALUE_FORMATTERS: dict[str, Callable[[int | float, str | None], str]] = {
    "relay_on_time": lambda value, unit: format_seconds_as_human_time(value),
}


def format_seconds_as_human_time(value: int | float) -> str:
    return get_humanized_timedelta(timedelta(seconds=value))

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

        latest_logs = await SensorLog.get_latest_log_per_device()
        if not latest_logs:
            await update_message(
                client,
                command,
                context,
                text="No sensor readings found.",
            )
            logger.info("No sensor readings found")
            return

        logs = select_devices_to_render(latest_logs)

        for log in logs:
            logger.info(f"Latest sensor log for {log.device}: {get_sensor_data(log)} at {log.timestamp}")

        units_by_device = await SensorUnit.get_for_devices([log.device for log in logs])
        if not units_by_device:
            await update_message(
                client,
                command,
                context,
                text="No sensor units found.",
            )
            logger.info(f"No sensor units found for devices {[log.device for log in logs]}")
            return

        mode = context.get("howfresh_mode", get_command_mode(command))
        message_blocks = build_sensor_message_blocks(logs, units_by_device, detailed=mode == "detailed")

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


def reading_age(sensor_log: "SensorLog") -> timedelta:
    # MongoDB stores dates without a zone, so a round-tripped document comes back naive even
    # though it was written as UTC. Assume UTC rather than subtracting against a naive now(),
    # which would silently read as local time.
    timestamp = sensor_log.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)

    return datetime.now(UTC) - timestamp


def is_stale(sensor_log: "SensorLog") -> bool:
    return reading_age(sensor_log) > device_config.stale_after_for(sensor_log.device)


def is_excluded(sensor_log: "SensorLog") -> bool:
    exclude_after = device_config.exclude_after_for(sensor_log.device)
    return exclude_after is not None and reading_age(sensor_log) > exclude_after


def select_devices_to_render(latest_logs: list["SensorLog"]) -> list["SensorLog"]:
    """
    Drop devices whose newest reading is too old to describe the space now.

    A device silent past its exclude_after has most likely been unplugged or reflashed, and a
    column of week-old values is just noise next to live ones. If every device is that stale
    they are all kept: a stale readout beats "no sensor readings found" when readings exist,
    and the stale marker already says not to trust them. So a device is only ever dropped
    while another is still reporting.
    """
    included = [log for log in latest_logs if not is_excluded(log)]

    if not included:
        logger.info("Every device is past its exclusion threshold - rendering them all, marked stale")
        return sort_devices(latest_logs)

    dropped = [log.device for log in latest_logs if log not in included]
    if dropped:
        logger.info(f"Excluding devices with readings past their exclusion threshold: {dropped}")

    return sort_devices(included)


def sort_devices(sensor_logs: list["SensorLog"]) -> list["SensorLog"]:
    """
    Put the columns in a configured, stable order.

    The query returns devices by reading time, so without this the columns would swap around
    between invocations depending on which device reported most recently.
    """
    return sorted(sensor_logs, key=lambda sensor_log: device_config.sort_key_for(sensor_log.device))


def device_label(sensor_log: "SensorLog") -> str:
    """Friendly name if one is configured, otherwise the raw hostname."""
    return device_config.display_name(sensor_log.device)


def build_sensor_message_blocks(
        sensor_logs: list["SensorLog"],
        units_by_device: dict[str, "SensorUnit"],
        *,
        detailed: bool,
) -> list[Block]:
    # One device needs no table - a table exists to compare devices, and the per-device
    # columns and sensor-suffixed labels cost width for nothing. This is also the state of
    # the space today, and the state again whenever a device drops off, so it is the normal
    # path rather than a fallback.
    if len(sensor_logs) == 1:
        sensor_log = sensor_logs[0]
        units = units_by_device.get(sensor_log.device)

        if detailed:
            logger.info("Running detailed mode for /howfresh command (single device)")
            return build_detailed_sensor_message_blocks(sensor_log, units)

        logger.info("Running default mode for /howfresh command (single device)")
        return build_summary_sensor_message_blocks(sensor_log, units)

    if detailed:
        logger.info(f"Running detailed mode for /howfresh command ({len(sensor_logs)} devices)")
        return build_detailed_sensor_table_blocks(sensor_logs, units_by_device)

    logger.info(f"Running default mode for /howfresh command ({len(sensor_logs)} devices)")
    return build_summary_sensor_table_blocks(sensor_logs, units_by_device)


def build_message_header(sensor_log: "SensorLog", *, title: str = "Sensor Readings") -> list[Block]:
    return [
        SectionBlock(text=MarkdownTextObject(text=f"*{title} ({device_label(sensor_log)}):*\n"
                                                  f"_Last updated {get_humanized_time(sensor_log.timestamp)}_")),
        DividerBlock(),
    ]


def get_sensor_data(sensor_log: "SensorLog") -> dict[str, dict[str, int | float]]:
    return sensor_log.data.model_dump()


def get_units_data(units: "SensorUnit | None") -> dict[str, dict[str, str]]:
    # A device can report readings before its units document exists, so a missing one must
    # degrade to unitless values rather than failing the whole readout.
    if units is None:
        return {}

    return units.sensors.model_dump()


def get_sensor_sort_key(name: str) -> tuple[int, str]:
    return SENSOR_SORT_ORDER.get(name, len(SENSOR_SORT_ORDER)), name


def get_measurement_sort_key(name: str) -> tuple[int, str, str]:
    normalized_name = normalize_measurement_key(name)
    order = MEASUREMENT_SORT_ORDER.get(name, MEASUREMENT_SORT_ORDER.get(normalized_name, len(MEASUREMENT_SORT_ORDER)))
    return order, normalized_name, name


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

def get_sensor_label(name: str) -> str:
    return SENSOR_NAME_FORMATS.get(name, name)


def normalize_measurement_unit(unit: str | None) -> str:
    if not unit:
        return ""

    normalized_unit = unit.strip().lower()
    return MEASUREMENT_UNIT_FORMATS.get(normalized_unit, unit)


def format_measurement_value(value: int | float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return f"{value:.2f}" if isinstance(value, float) else str(value)


def format_measurement_with_unit(value: int | float, unit: str | None) -> str:
    formatted_value = format_measurement_value(value)
    formatted_unit = normalize_measurement_unit(unit)

    if not formatted_unit:
        return formatted_value

    return f"{formatted_value} {formatted_unit}"


def format_measurement_reading(measurement_name: str, value: int | float, unit: str | None) -> str:
    normalized_name = normalize_measurement_key(measurement_name)
    formatter = MEASUREMENT_VALUE_FORMATTERS.get(normalized_name)

    if formatter:
        return formatter(value, unit)

    return format_measurement_with_unit(value, unit)


def format_measurement_line(
        measurement_name: str,
        value: int | float,
        unit: str | None,
        *,
        suffix: str | None = None
) -> str:
    symbol = get_measurement_symbol(measurement_name)
    display_name = normalize_measurement_name(measurement_name)
    formatted_measurement = format_measurement_reading(measurement_name, value, unit)

    suffix_text = f" ({suffix})" if suffix else ""

    return f"{symbol} *{display_name}{suffix_text}*: {formatted_measurement}"


def build_detailed_sensor_message_blocks(sensor_log: "SensorLog", units: "SensorUnit") -> list[Block]:
    blocks = build_message_header(sensor_log)

    sensor_data = get_sensor_data(sensor_log)
    units_data = get_units_data(units)

    for sensor_name in sorted(sensor_data, key=get_sensor_sort_key):
        readings = sensor_data[sensor_name]
        sensor_label = get_sensor_label(sensor_name)
        sensor_lines = [f"*{sensor_label}*"]
        sensor_units = units_data.get(sensor_name, {})

        for measurement_name in sorted(readings, key=get_measurement_sort_key):
            value = readings[measurement_name]
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
        line
        for measurement_name in SUMMARY_MEASUREMENTS
        if (line := format_summary_measurement_line(measurement_name, summary_readings))
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

    for sensor_name in sorted(sensor_data, key=get_sensor_sort_key):
        readings = sensor_data[sensor_name]
        sensor_units = units_data.get(sensor_name, {})

        for measurement_name in sorted(readings, key=get_measurement_sort_key):
            value = readings[measurement_name]
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
) -> str | None:
    summary_measurement_name = normalize_measurement_key(measurement_name)
    summary_reading = summary_readings.get(summary_measurement_name)
    if not summary_reading:
        return None

    values = summary_reading["values"]
    unit = summary_reading["unit"]

    if not values:
        return None

    average_value = sum(values) / len(values)

    suffix = "avg" if len(values) > 1 else None

    return format_measurement_line(
        summary_measurement_name,
        average_value,
        unit,
        suffix=suffix,
    )


def remove_trailing_divider(blocks: list[Block]) -> None:
    if blocks and isinstance(blocks[-1], DividerBlock):
        blocks.pop()


# --- Multi-device table rendering ---
#
# With more than one device reporting, measurements become rows and devices become columns.
# That way adding a sensor to a device fills in an existing row rather than restructuring the
# message, and the comparison that matters - the same measurement across the space - sits
# side by side. Table cells are raw_text or rich_text only, never mrkdwn, so the cell
# contents are built from the value formatters rather than from format_measurement_line.

EMPTY_CELL = "—"
STALE_MARKER = "⚠️"
READING_TIME_LABEL = "🕒 Reading taken"


def raw_cell(text: object) -> RawTextObject:
    return RawTextObject(text=str(text))


def header_cell(text: object) -> RawTextObject | RichTextBlock:
    """
    Bold header cell.

    A raw_text cell carries no styling at all, so a bold header has to be a rich_text cell.
    An empty header stays raw_text, since a rich text section needs at least one element.
    """
    if not str(text):
        return RawTextObject(text=" ")

    return RichTextBlock(
        elements=[
            RichTextSectionElement(
                elements=[
                    RichTextElementParts.Text(
                        text=str(text),
                        style=RichTextElementParts.TextStyle(bold=True),
                    )
                ]
            )
        ]
    )


def build_column_settings(device_count: int) -> list[TableBlockColumnSettings]:
    """Left-aligned labels, right-aligned values so units line up down each column."""
    return [TableBlockColumnSettings(align="left", is_wrapped=False)] + [
        TableBlockColumnSettings(align="right") for _ in range(device_count)
    ]


def build_device_header_row(sensor_logs: list["SensorLog"]) -> list[RawTextObject | RichTextBlock]:
    cells: list[RawTextObject | RichTextBlock] = [header_cell("")]

    for sensor_log in sensor_logs:
        label = device_label(sensor_log)
        cells.append(header_cell(f"{label} {STALE_MARKER}" if is_stale(sensor_log) else label))

    return cells


def build_reading_time_row(sensor_logs: list["SensorLog"]) -> list[RawTextObject | RichTextBlock]:
    """
    Reading age as its own row, one cell per device.

    Devices push on independent schedules, so a single "last updated" line in the header
    would have to describe either the freshest or the oldest column and would misrepresent
    the other.
    """
    return [raw_cell(READING_TIME_LABEL)] + [
        raw_cell(get_humanized_time(sensor_log.timestamp)) for sensor_log in sensor_logs
    ]


def build_stale_footnote(sensor_logs: list["SensorLog"]) -> ContextBlock | None:
    stale_logs = [sensor_log for sensor_log in sensor_logs if is_stale(sensor_log)]

    if not stale_logs:
        return None

    # Each device's own age rather than a shared threshold, which would be wrong for any
    # device carrying a per-device override.
    ages = ", ".join(
        f"{device_label(sensor_log)} {get_humanized_time(sensor_log.timestamp)}"
        for sensor_log in stale_logs
    )

    return ContextBlock(
        elements=[MarkdownTextObject(text=f"{STALE_MARKER} _Last reported: {ages} – these readings may be stale._")]
    )


def collect_device_summary_readings(
        sensor_log: "SensorLog",
        units: "SensorUnit | None",
) -> dict[str, SummaryReading]:
    return collect_summary_readings(sensor_log, units)


def build_summary_sensor_table_blocks(
        sensor_logs: list["SensorLog"],
        units_by_device: dict[str, "SensorUnit"],
) -> list[Block]:
    summaries = {
        sensor_log.device: collect_device_summary_readings(sensor_log, units_by_device.get(sensor_log.device))
        for sensor_log in sensor_logs
    }

    rows = [build_device_header_row(sensor_logs), build_reading_time_row(sensor_logs)]

    for measurement_name in SUMMARY_MEASUREMENTS:
        summary_measurement_name = normalize_measurement_key(measurement_name)
        cells: list[RawTextObject | RichTextBlock] = [
            raw_cell(f"{get_measurement_symbol(summary_measurement_name)} "
                     f"{normalize_measurement_name(summary_measurement_name)}")
        ]
        reported_anywhere = False

        for sensor_log in sensor_logs:
            summary_reading = summaries[sensor_log.device].get(summary_measurement_name)

            if not summary_reading or not summary_reading["values"]:
                cells.append(raw_cell(EMPTY_CELL))
                continue

            reported_anywhere = True
            values = summary_reading["values"]
            rendered = format_measurement_with_unit(sum(values) / len(values), summary_reading["unit"])

            # "(avg)" belongs on the cell, not the row label: one device may average two
            # sensors for a measurement while another reports a single reading for it.
            cells.append(raw_cell(f"{rendered} (avg)" if len(values) > 1 else rendered))

        if reported_anywhere:
            rows.append(cells)

    blocks: list[Block] = [
        SectionBlock(text=MarkdownTextObject(text="*Sensor Readings:*")),
        TableBlock(rows=rows, column_settings=build_column_settings(len(sensor_logs))),
    ]

    if (footnote := build_stale_footnote(sensor_logs)) is not None:
        blocks.append(footnote)

    blocks.append(
        ContextBlock(elements=[MarkdownTextObject(text="_For detailed sensor readings, use `/howfresh detailed`._")])
    )

    return blocks


def build_detailed_sensor_table_blocks(
        sensor_logs: list["SensorLog"],
        units_by_device: dict[str, "SensorUnit"],
) -> list[Block]:
    data_by_device = {sensor_log.device: get_sensor_data(sensor_log) for sensor_log in sensor_logs}
    units_data_by_device = {
        sensor_log.device: get_units_data(units_by_device.get(sensor_log.device)) for sensor_log in sensor_logs
    }

    # Row identity is (sensor, measurement). The sensor has to be part of it because
    # measurement names collide across sensors - BME280's `humidity` and SCD30's
    # `relative_humidity` both display as "Humidity", and `temperature` collides outright.
    # Grouped sections disambiguate those with a sensor heading; a flat table has none.
    pairs: list[tuple[str, str]] = []
    for sensor_data in data_by_device.values():
        for sensor_name, readings in sensor_data.items():
            for measurement_name in readings:
                if (sensor_name, measurement_name) not in pairs:
                    pairs.append((sensor_name, measurement_name))

    pairs.sort(key=lambda pair: (get_sensor_sort_key(pair[0]), get_measurement_sort_key(pair[1])))

    rows = [build_device_header_row(sensor_logs), build_reading_time_row(sensor_logs)]

    for sensor_name, measurement_name in pairs:
        label = (
            f"{get_measurement_symbol(measurement_name)} "
            f"{normalize_measurement_name(measurement_name)} ({sensor_name})"
        )
        cells: list[RawTextObject | RichTextBlock] = [raw_cell(label)]

        for sensor_log in sensor_logs:
            readings = data_by_device[sensor_log.device].get(sensor_name, {})

            if measurement_name not in readings:
                cells.append(raw_cell(EMPTY_CELL))
                continue

            unit = units_data_by_device[sensor_log.device].get(sensor_name, {}).get(measurement_name)
            cells.append(raw_cell(format_measurement_reading(measurement_name, readings[measurement_name], unit)))

        rows.append(cells)

    blocks: list[Block] = [
        SectionBlock(text=MarkdownTextObject(text="*Sensor Readings* — _detailed_")),
        TableBlock(rows=rows, column_settings=build_column_settings(len(sensor_logs))),
    ]

    if (footnote := build_stale_footnote(sensor_logs)) is not None:
        blocks.append(footnote)

    return blocks
