"""
Generate Block Kit payloads for the proposed tabular /howfresh output.

Paste the generated JSON into https://app.slack.com/block-kit-builder to check how the
layout actually renders. The SDK's validate_json() only enforces its own schema rules - it
does not tell you whether a workspace renders a table block at all, or how wide the label
column gets on a phone. Those need eyes on Slack.

The payloads deliberately reuse the real formatting helpers from plugins.space.howfresh
(symbols, display names, unit prettification, sort order, the relay_on_time formatter), so
what you paste matches what SMIB would post rather than a hand-written approximation of it.
Only the table assembly is new - that is the part under design.

Usage:
    python scripts/generate_howfresh_block_payloads.py [--output-dir DIR] [--print]

Context: https://github.com/somakeit/smib/issues/510 - a second SMIBHID device is being
installed in the space, and /howfresh currently renders a single arbitrary device.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from slack_sdk.models.blocks import (  # noqa: E402
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

from smib.utilities import get_humanized_time  # noqa: E402

from plugins.space.howfresh import (  # noqa: E402
    SUMMARY_MEASUREMENTS,
    format_measurement_line,
    format_measurement_reading,
    format_measurement_with_unit,
    get_measurement_sort_key,
    get_measurement_symbol,
    get_sensor_label,
    get_sensor_sort_key,
    normalize_measurement_key,
    normalize_measurement_name,
    remove_trailing_divider,
)

# An empty cell needs to read as "this device does not report that", not as a zero or a
# missing value. An em dash is the current proposal; a blank cell or "n/a" may read better.
EMPTY_CELL = "—"

# Two devices as the space is about to be configured: the existing full sensor suite, plus a
# newly installed unit that initially reports light only (temperature and particulate to
# follow). The friendly names are what the device map in config supplies; without an entry a
# device falls back to its raw hostname.
DEVICE_READINGS: dict[str, dict[str, dict[str, int | float]]] = {
    "Cleanroom": {
        "BH1750": {"light": 310.0},
        "BME280": {"temperature": 21.4, "humidity": 42.0, "pressure": 1013.2},
        "SCD30": {"co2": 480.2, "temperature": 21.9, "relative_humidity": 41.1},
        "PMSA003I": {
            "pm10_standard": 5,
            "pm25_standard": 6,
            "pm100_standard": 6,
            "particles_03um": 744,
            "particles_05um": 232,
        },
        "InternalMetrics": {"relay_on_time": 1741003},
    },
    "Workshop": {
        "BH1750": {"light": 180.0},
    },
    # Long-abandoned unit: still has a stored reading, but has not reported in over a week.
    # Exercises the exclusion path - the values are real but far too old to answer "how
    # fresh is the space right now?", and a column of them is only noise.
    "Spare": {
        "BME280": {"temperature": 16.2, "humidity": 55.0},
    },
}

SENSOR_UNITS: dict[str, dict[str, str]] = {
    "BH1750": {"light": "lx"},
    "BME280": {"temperature": "C", "humidity": "%", "pressure": "hPa"},
    "SCD30": {"co2": "ppm", "temperature": "C", "relative_humidity": "%"},
    "PMSA003I": {
        "pm10_standard": "ug/m3",
        "pm25_standard": "ug/m3",
        "pm100_standard": "ug/m3",
        "particles_03um": "count/0.1L",
        "particles_05um": "count/0.1L",
    },
    "InternalMetrics": {"relay_on_time": "s"},
}

# Each device pushes on its own schedule, so the readings in one column were not necessarily
# taken at the same moment as the next column's. Deliberately staggered here to exercise all
# three freshness bands: fresh, stale-but-shown, and dropped entirely.
DEVICE_REPORTED_AT: dict[str, datetime] = {
    "Cleanroom": datetime.now(UTC) - timedelta(minutes=2),
    "Workshop": datetime.now(UTC) - timedelta(minutes=47),
    "Spare": datetime.now(UTC) - timedelta(days=9),
}

# Two thresholds, because "old enough to flag" and "old enough to be useless" are different
# questions. Between them a device still answers "how fresh is the space?" as long as the
# answer is labelled; past the second it is only noise in a column, and the device has most
# likely been unplugged or reflashed rather than being briefly offline.
#
# Both are placeholders for the demo. The real implementation should default STALE_AFTER to
# the existing SMIB_PLUGIN_SMIBHID_SENSOR_MONITOR_ALERT_THRESHOLD (1 hour) rather than
# introducing a second notion of "too old" that can disagree with the one the sensor log
# monitor already alerts on. EXCLUDE_AFTER has no existing equivalent and needs its own
# setting - erring long, since dropping a device is the more destructive of the two actions.
STALE_AFTER = timedelta(minutes=30)
EXCLUDE_AFTER = timedelta(days=2)

STALE_MARKER = "⚠️"


TableCell = RawTextObject | RichTextBlock


def reading_age(device: str) -> timedelta:
    return datetime.now(UTC) - DEVICE_REPORTED_AT[device]


def is_stale(device: str) -> bool:
    return STALE_AFTER < reading_age(device) <= EXCLUDE_AFTER


def is_excluded(device: str) -> bool:
    return reading_age(device) > EXCLUDE_AFTER


def included_devices(devices: list[str]) -> list[str]:
    """
    Devices worth rendering at all.

    If every device is past EXCLUDE_AFTER, none are dropped: a readout of stale data beats
    "no sensor readings found" when readings do exist, and the stale marker already says not
    to trust them. Only ever drops a device when some other device is still reporting.
    """
    included = [device for device in devices if not is_excluded(device)]

    return included or devices


def device_header(device: str) -> str:
    return f"{device} {STALE_MARKER}" if is_stale(device) else device


def reported_at_text(device: str) -> str:
    return get_humanized_time(DEVICE_REPORTED_AT[device])


def raw_cell(text: Any) -> RawTextObject:
    return RawTextObject(text=str(text))


def header_cell(text: Any) -> TableCell:
    """
    Bold header cell.

    A raw_text cell carries no styling - RawTextObject.attributes is {"text", "type"} - so a
    bold header has to be a rich_text cell instead. Table cells accept either, and an empty
    header falls back to raw_text because a rich text section needs at least one element.
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


def column_settings(device_count: int) -> list[TableBlockColumnSettings]:
    """Left-aligned labels, right-aligned values so units line up down each column."""
    return [TableBlockColumnSettings(align="left", is_wrapped=False)] + [
        TableBlockColumnSettings(align="right") for _ in range(device_count)
    ]


def measurement_label(measurement: str, sensor: str | None = None) -> str:
    symbol = get_measurement_symbol(measurement)
    name = normalize_measurement_name(measurement)

    if sensor is None:
        return f"{symbol} {name}"

    # The sensor suffix is what keeps row labels unique. BME280 reports `humidity` while
    # SCD30 reports `relative_humidity`, and both normalize to the label "Humidity";
    # `temperature` collides outright. Grouped sections disambiguate those today via the
    # sensor heading, but a flat table has no heading to inherit, so the sensor moves into
    # the label itself. Always shown rather than only on collision, so a given measurement
    # always reads the same regardless of which sensors happen to be reporting.
    return f"{symbol} {name} ({sensor})"


def collect_device_summary(device: str) -> dict[str, dict[str, Any]]:
    """
    Average each summary measurement within a single device, across its sensors.

    Mirrors collect_summary_readings in the plugin: readings are merged on the normalized
    measurement key, so `humidity` and `relative_humidity` land together.
    """
    collected: dict[str, dict[str, Any]] = {}

    for sensor, readings in DEVICE_READINGS[device].items():
        for measurement, value in readings.items():
            key = normalize_measurement_key(measurement)
            if key not in {normalize_measurement_key(m) for m in SUMMARY_MEASUREMENTS}:
                continue

            entry = collected.setdefault(key, {"values": [], "unit": None})
            entry["values"].append(value)

            if entry["unit"] is None:
                entry["unit"] = SENSOR_UNITS.get(sensor, {}).get(measurement)

    return collected


def build_summary_rows(devices: list[str]) -> list[list[TableCell]]:
    # The first header cell is left empty - the rows are self-evidently measurements, and the
    # label column is the one that runs out of width first on mobile.
    rows = [[header_cell("")] + [header_cell(device_header(device)) for device in devices]]

    # Reading age goes in its own row, per device, rather than once in the message header.
    # Devices push on independent schedules, so a single "last updated" in the header would
    # have to describe the freshest or the oldest column and would misrepresent the other.
    rows.append([raw_cell("🕒 Reading taken")] + [raw_cell(reported_at_text(d)) for d in devices])

    per_device = {device: collect_device_summary(device) for device in devices}

    for measurement in SUMMARY_MEASUREMENTS:
        key = normalize_measurement_key(measurement)
        cells = [raw_cell(measurement_label(key))]
        reported_anywhere = False

        for device in devices:
            entry = per_device[device].get(key)

            if not entry or not entry["values"]:
                cells.append(raw_cell(EMPTY_CELL))
                continue

            reported_anywhere = True
            values = entry["values"]
            rendered = format_measurement_with_unit(sum(values) / len(values), entry["unit"])

            # "(avg)" belongs on the cell, not the row: one device may average two sensors
            # while another reports a single reading for the same measurement.
            cells.append(raw_cell(f"{rendered} (avg)" if len(values) > 1 else rendered))

        if reported_anywhere:
            rows.append(cells)

    return rows


def build_detailed_rows(devices: list[str]) -> list[list[TableCell]]:
    # Row identity is (sensor, measurement) - the pair is what the suffixed label encodes.
    pairs: list[tuple[str, str]] = []
    for device_data in DEVICE_READINGS.values():
        for sensor, readings in device_data.items():
            for measurement in readings:
                if (sensor, measurement) not in pairs:
                    pairs.append((sensor, measurement))

    pairs.sort(key=lambda pair: (get_sensor_sort_key(pair[0]), get_measurement_sort_key(pair[1])))

    rows = [[header_cell("")] + [header_cell(device_header(device)) for device in devices]]

    # Reading age goes in its own row, per device, rather than once in the message header.
    # Devices push on independent schedules, so a single "last updated" in the header would
    # have to describe the freshest or the oldest column and would misrepresent the other.
    rows.append([raw_cell("🕒 Reading taken")] + [raw_cell(reported_at_text(d)) for d in devices])

    for sensor, measurement in pairs:
        cells = [raw_cell(measurement_label(measurement, sensor))]

        for device in devices:
            readings = DEVICE_READINGS[device].get(sensor, {})

            if measurement not in readings:
                cells.append(raw_cell(EMPTY_CELL))
                continue

            unit = SENSOR_UNITS.get(sensor, {}).get(measurement)
            cells.append(raw_cell(format_measurement_reading(measurement, readings[measurement], unit)))

        rows.append(cells)

    return rows


def build_single_device_blocks(device: str, *, detailed: bool) -> list[Block]:
    """
    One device: keep the existing mrkdwn section layout rather than a one-column table.

    A table whose only purpose is comparing devices has nothing to compare, and the format
    costs real width - the sensor suffix exists solely to keep row labels unique across
    devices, and the label column is the first thing to break on a phone. This is also not
    an edge case: it is the current state of the space, and the state again whenever the
    second device drops off, so it has to look deliberate rather than degraded.

    The lines are built by the plugin's own formatters, so a single-device readout is
    byte-identical to what /howfresh produces today apart from the friendly device name.
    """
    header = "*How fresh is the space?*" + (" — _detailed_" if detailed else "")
    blocks: list[Block] = [
        SectionBlock(
            text=MarkdownTextObject(
                text=f"{header}\n_{device} · reading taken {reported_at_text(device)}_"
            )
        ),
        DividerBlock(),
    ]

    if detailed:
        for sensor in sorted(DEVICE_READINGS[device], key=get_sensor_sort_key):
            readings = DEVICE_READINGS[device][sensor]
            lines = [f"*{get_sensor_label(sensor)}*"]

            for measurement in sorted(readings, key=get_measurement_sort_key):
                unit = SENSOR_UNITS.get(sensor, {}).get(measurement)
                lines.append(format_measurement_line(measurement, readings[measurement], unit))

            blocks.append(SectionBlock(text=MarkdownTextObject(text="\n".join(lines))))
            blocks.append(DividerBlock())

        remove_trailing_divider(blocks)
        return blocks

    summary = collect_device_summary(device)
    lines = []
    for measurement in SUMMARY_MEASUREMENTS:
        entry = summary.get(normalize_measurement_key(measurement))
        if not entry or not entry["values"]:
            continue

        values = entry["values"]
        lines.append(
            format_measurement_line(
                measurement,
                sum(values) / len(values),
                entry["unit"],
                suffix="avg" if len(values) > 1 else None,
            )
        )

    blocks.append(
        SectionBlock(
            text=MarkdownTextObject(text="\n".join(lines) if lines else "No summary sensor readings found.")
        )
    )

    if (footnote := stale_footnote([device])) is not None:
        blocks.append(footnote)

    blocks.append(DividerBlock())
    blocks.append(
        SectionBlock(
            text=MarkdownTextObject(text="_For detailed sensor readings, use `/howfresh detailed`._")
        )
    )

    return blocks


def stale_footnote(devices: list[str]) -> ContextBlock | None:
    """
    Spell out what the marker in a column header means, naming the devices it applies to.

    Stale readings are marked and kept rather than hidden: dropping a column entirely would
    be a regression from today's output, which shows whatever the last report held however
    old it is. Marked-and-shown beats silently absent.
    """
    stale_devices = [device for device in devices if is_stale(device)]

    if not stale_devices:
        return None

    names = ", ".join(stale_devices)
    return ContextBlock(
        elements=[
            MarkdownTextObject(
                text=f"{STALE_MARKER} _{names} last reported over "
                     f"{int(STALE_AFTER.total_seconds() // 60)} minutes ago - readings may be stale._"
            )
        ]
    )


def build_summary_blocks(devices: list[str]) -> list[Block]:
    devices = included_devices(devices)

    if len(devices) == 1:
        return build_single_device_blocks(devices[0], detailed=False)

    blocks: list[Block] = [
        SectionBlock(text=MarkdownTextObject(text="*How fresh is the space?*")),
        TableBlock(rows=build_summary_rows(devices), column_settings=column_settings(len(devices))),
    ]

    if (footnote := stale_footnote(devices)) is not None:
        blocks.append(footnote)

    blocks.append(
        ContextBlock(
            elements=[MarkdownTextObject(text="_For all sensor readings, use `/howfresh detailed`._")]
        )
    )

    return blocks


def build_detailed_blocks(devices: list[str]) -> list[Block]:
    devices = included_devices(devices)

    if len(devices) == 1:
        return build_single_device_blocks(devices[0], detailed=True)

    blocks: list[Block] = [
        SectionBlock(text=MarkdownTextObject(text="*How fresh is the space?* — _detailed_")),
        TableBlock(rows=build_detailed_rows(devices), column_settings=column_settings(len(devices))),
    ]

    if (footnote := stale_footnote(devices)) is not None:
        blocks.append(footnote)

    return blocks


def cell_text(cell: TableCell) -> str:
    """Pull the display text back out of a cell, for the terminal preview only."""
    if isinstance(cell, RawTextObject):
        return cell.text

    return "".join(
        part.text
        for element in cell.elements
        for part in getattr(element, "elements", [])
        if getattr(part, "text", None)
    )


def render_ascii_preview(rows: list[list[TableCell]], title: str) -> str:
    """
    Rough terminal preview. Emoji are double-width in most terminals, so the pipes look
    ragged - that is a preview artifact, not the Slack layout. Useful for row/column counts
    and label lengths, not for judging alignment.
    """
    text_rows = [[cell_text(cell) for cell in row] for row in rows]
    widths = [max(len(row[index]) for row in text_rows) for index in range(len(text_rows[0]))]

    lines = [f"--- {title} ---"]
    for row_index, row in enumerate(text_rows):
        cells = [
            text.ljust(widths[index]) if index == 0 else text.rjust(widths[index])
            for index, text in enumerate(row)
        ]
        lines.append(" | ".join(cells))
        if row_index == 0:
            lines.append("-+-".join("-" * width for width in widths))

    lines.append(f"({len(rows) - 1} rows x {len(rows[0])} columns, widest label {widths[0]} chars)")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "scripts" / "block_payloads",
        help="Directory to write the payload JSON into (default: scripts/block_payloads)",
    )
    parser.add_argument("--print", action="store_true", help="Print the payload JSON to stdout as well")
    args = parser.parse_args()

    devices = list(DEVICE_READINGS)

    # "Spare" is past EXCLUDE_AFTER, so the multi-device payloads drop it; the single-device
    # payloads pass one device explicitly to show the layout /howfresh falls back to.
    payloads = {
        "howfresh_summary_table": build_summary_blocks(devices),
        "howfresh_detailed_table": build_detailed_blocks(devices),
        "howfresh_summary_single_device": build_summary_blocks(["Cleanroom"]),
        "howfresh_detailed_single_device": build_detailed_blocks(["Cleanroom"]),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for name, blocks in payloads.items():
        for block in blocks:
            # Catches a malformed payload here rather than as a Slack API error.
            block.validate_json()

        payload = {"blocks": [block.to_dict() for block in blocks]}
        output_path = args.output_dir / f"{name}.json"
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        print(f"wrote {output_path.relative_to(REPO_ROOT)}")

        if args.print:
            print(json.dumps(payload, indent=2, ensure_ascii=False))

    rendered = included_devices(devices)
    dropped = [device for device in devices if device not in rendered]

    print()
    print(f"devices: {', '.join(devices)}")
    print(f"  rendered: {', '.join(rendered)}")
    print(f"  stale (shown, marked): {', '.join(d for d in rendered if is_stale(d)) or '-'}")
    print(f"  dropped (over {EXCLUDE_AFTER.days}d): {', '.join(dropped) or '-'}")
    print()
    print(render_ascii_preview(build_summary_rows(rendered), "SUMMARY"))
    print()
    print(render_ascii_preview(build_detailed_rows(rendered), "DETAILED"))
    print()
    print("--- SINGLE DEVICE (non-tabular fallback) ---")
    for block in build_summary_blocks(["Cleanroom"]):
        payload = block.to_dict()
        if payload["type"] == "section":
            print(payload["text"]["text"])
        elif payload["type"] == "context":
            print(payload["elements"][0]["text"])
        else:
            print(f"[{payload['type']}]")


if __name__ == "__main__":
    main()
