"""
Unit tests for the /howfresh message rendering in plugins.space.howfresh.

These cover the pure formatting and aggregation helpers - value/unit formatting, measurement
naming, sort ordering, summary collection and the assembled block structure. They deliberately
avoid the DB and Slack: build_sensor_message_blocks takes a SensorLog and SensorUnit and
returns blocks, so the whole render is reachable without Mongo or a WebClient. The command
handlers themselves (how_fresh_loading/how_fresh) are chat_postMessage/chat_update wrappers
around these helpers and are left out.

Context - this is the first test coverage for /howfresh, written ahead of a second SMIBHID
device being installed in the space (see https://github.com/somakeit/smib/issues/510). The
current render pulls `SensorLog.get_latest_log()` with no device filter, so these tests pin
down the existing single-device behaviour before multi-device/zoning changes the shape of the
message. Several tests below assert on cross-sensor averaging, which is the mechanism that
cross-device averaging will have to reuse or deliberately replace.
"""

from datetime import UTC, datetime, timedelta

import pytest
from slack_sdk.models.blocks import DividerBlock, SectionBlock

from plugins.space.howfresh import (
    MEASUREMENT_SORT_ORDER,
    SUMMARY_MEASUREMENTS,
    build_sensor_message_blocks,
    collect_summary_readings,
    format_measurement_line,
    format_measurement_reading,
    format_measurement_value,
    format_measurement_with_unit,
    format_seconds_as_human_time,
    format_summary_measurement_line,
    get_measurement_sort_key,
    get_measurement_symbol,
    get_sensor_label,
    get_sensor_sort_key,
    normalize_measurement_key,
    normalize_measurement_name,
    normalize_measurement_unit,
    remove_trailing_divider,
)
from plugins.space.smibhid.sensor.models import (
    SensorDataMap,
    SensorLog,
    SensorUnit,
    SensorUnitMap,
)

T0 = datetime(2026, 11, 25, 18, 0, 0, tzinfo=UTC)


def make_sensor_log(data: dict, *, device: str = "SMIBHID-TEST", timestamp: datetime = T0) -> SensorLog:
    """
    A SensorLog as the /smibhid/log/sensor route builds it.

    model_construct is used deliberately - SensorLog is a Beanie Document, and normal
    instantiation requires an initialized Mongo collection. The render helpers only read
    `.data`, `.device` and `.timestamp`, so a constructed model exercises them faithfully
    without standing up a database. `data` is still validated through SensorDataMap so a
    malformed fixture fails here rather than silently rendering.
    """
    return SensorLog.model_construct(
        device=device,
        timestamp=timestamp,
        received_timestamp=timestamp,
        data=SensorDataMap.model_validate(data),
    )


def make_sensor_units(sensors: dict, *, device: str = "SMIBHID-TEST") -> SensorUnit:
    return SensorUnit.model_construct(
        device=device,
        sensors=SensorUnitMap.model_validate(sensors),
    )


def section_texts(blocks) -> list[str]:
    return [b.text.text for b in blocks if isinstance(b, SectionBlock)]


def rendered_text(blocks) -> str:
    return "\n".join(section_texts(blocks))


class TestFormatMeasurementValue:
    def test_integral_float_loses_the_pointless_decimals(self):
        """A 200.0 lux reading should read as '200', not '200.00'."""
        assert format_measurement_value(200.0) == "200"

    def test_non_integral_float_is_fixed_to_two_places(self):
        assert format_measurement_value(39.5512) == "39.55"

    def test_int_is_passed_through_unchanged(self):
        assert format_measurement_value(744) == "744"

    def test_rounding_is_applied_not_truncation(self):
        assert format_measurement_value(1.006) == "1.01"

    def test_zero_renders_as_zero_not_empty(self):
        assert format_measurement_value(0) == "0"
        assert format_measurement_value(0.0) == "0"

    def test_negative_values_keep_their_sign(self):
        """Outdoor temperature can legitimately go below zero."""
        assert format_measurement_value(-3.25) == "-3.25"


class TestNormalizeMeasurementUnit:
    @pytest.mark.parametrize(
        "raw_unit, expected",
        [
            ("C", "°C"),
            ("c", "°C"),
            ("degC", "°C"),
            ("celsius", "°C"),
            ("percent", "%"),
            ("ug/m3", "μg/m³"),
            ("ppm", "ppm"),
        ],
    )
    def test_known_units_are_prettified_case_insensitively(self, raw_unit, expected):
        assert normalize_measurement_unit(raw_unit) == expected

    def test_surrounding_whitespace_is_ignored(self):
        assert normalize_measurement_unit("  C  ") == "°C"

    def test_unknown_unit_is_preserved_verbatim(self):
        """SMIBHID may report units SMIB has no mapping for - don't mangle them."""
        assert normalize_measurement_unit("count/0.1L") == "count/0.1L"

    def test_missing_unit_becomes_empty_string(self):
        assert normalize_measurement_unit(None) == ""
        assert normalize_measurement_unit("") == ""


class TestFormatMeasurementWithUnit:
    def test_value_and_unit_are_space_separated(self):
        assert format_measurement_with_unit(29.0, "C") == "29 °C"

    def test_unitless_measurement_has_no_trailing_space(self):
        assert format_measurement_with_unit(744, None) == "744"


class TestMeasurementNaming:
    def test_relative_humidity_is_aliased_to_humidity(self):
        """
        SCD30 reports `relative_humidity` and BME280 reports `humidity`; the summary treats
        them as one measurement, so the alias has to resolve before lookup.
        """
        assert normalize_measurement_key("relative_humidity") == "humidity"

    def test_keys_are_lowercased_and_stripped(self):
        assert normalize_measurement_key("  Temperature ") == "temperature"

    def test_known_measurements_use_their_display_name(self):
        assert normalize_measurement_name("co2") == "CO₂"
        assert normalize_measurement_name("pm25_standard") == "PM2.5 (Standard)"

    def test_aliased_measurement_renders_as_its_target(self):
        assert normalize_measurement_name("relative_humidity") == "Humidity"

    def test_unknown_measurement_is_title_cased_from_snake_case(self):
        """A new sensor measurement should render readably with no code change."""
        assert normalize_measurement_name("soil_moisture") == "Soil Moisture"

    def test_known_measurement_has_a_symbol(self):
        assert get_measurement_symbol("temperature") == "🌡️"

    def test_aliased_measurement_inherits_the_symbol(self):
        assert get_measurement_symbol("relative_humidity") == "💧"

    def test_unknown_measurement_falls_back_to_a_bullet(self):
        assert get_measurement_symbol("soil_moisture") == "•"

    def test_known_sensor_uses_its_friendly_label(self):
        assert get_sensor_label("BME280") == "Climate (BME280)"

    def test_unknown_sensor_label_is_the_raw_name(self):
        assert get_sensor_label("SGP30") == "SGP30"


class TestSortOrdering:
    def test_known_sensors_sort_into_the_declared_order(self):
        names = ["InternalMetrics", "BME280", "BH1750"]
        assert sorted(names, key=get_sensor_sort_key) == ["BH1750", "BME280", "InternalMetrics"]

    def test_unknown_sensors_sort_last_and_alphabetically(self):
        names = ["SGP30", "BME280", "AAA999"]
        assert sorted(names, key=get_sensor_sort_key) == ["BME280", "AAA999", "SGP30"]

    def test_known_measurements_sort_into_the_declared_order(self):
        names = ["co2", "temperature", "pressure"]
        assert sorted(names, key=get_measurement_sort_key) == ["temperature", "pressure", "co2"]

    def test_aliased_measurement_sorts_on_its_own_entry(self):
        """
        `relative_humidity` has its own slot in MEASUREMENT_ORDER, so it must not be
        collapsed onto `humidity`'s position when sorting a detailed readout.
        """
        key = get_measurement_sort_key("relative_humidity")
        assert key[0] == MEASUREMENT_SORT_ORDER["relative_humidity"]

    def test_unknown_measurements_sort_last(self):
        names = ["soil_moisture", "temperature"]
        assert sorted(names, key=get_measurement_sort_key) == ["temperature", "soil_moisture"]


class TestRelayOnTimeFormatting:
    """
    relay_on_time arrives in seconds and is the one measurement with a bespoke formatter -
    a raw '1741003 s' is useless in Slack.
    """

    def test_seconds_render_as_human_time(self):
        assert format_seconds_as_human_time(timedelta(days=2, hours=3).total_seconds()) == "2 days and 3 hours"

    def test_relay_on_time_uses_the_custom_formatter_and_drops_the_unit(self):
        rendered = format_measurement_reading("relay_on_time", 7200, "s")

        assert "7200" not in rendered
        assert rendered == "2 hours"

    def test_other_measurements_fall_back_to_value_plus_unit(self):
        assert format_measurement_reading("temperature", 29.0, "C") == "29 °C"


class TestFormatMeasurementLine:
    def test_line_has_symbol_bold_name_and_formatted_value(self):
        assert format_measurement_line("temperature", 29.0, "C") == "🌡️ *Temperature*: 29 °C"

    def test_suffix_is_parenthesised_inside_the_bold_name(self):
        line = format_measurement_line("temperature", 29.7, "C", suffix="avg")

        assert line == "🌡️ *Temperature (avg)*: 29.70 °C"


class TestCollectSummaryReadings:
    def test_only_summary_measurements_are_collected(self):
        log = make_sensor_log(
            {
                "BME280": {"temperature": 21.0, "pressure": 1013.0},
                "PMSA003I": {"pm25_standard": 6},
            }
        )
        units = make_sensor_units({"BME280": {"temperature": "C", "pressure": "hPa"}})

        readings = collect_summary_readings(log, units)

        assert set(readings) == {"temperature"}

    def test_same_measurement_from_two_sensors_is_gathered_for_averaging(self):
        log = make_sensor_log(
            {
                "BME280": {"temperature": 29.0},
                "SCD30": {"temperature": 30.4},
            }
        )
        units = make_sensor_units({"BME280": {"temperature": "C"}, "SCD30": {"temperature": "C"}})

        readings = collect_summary_readings(log, units)

        assert readings["temperature"]["values"] == [29.0, 30.4]

    def test_aliased_humidity_is_merged_with_plain_humidity(self):
        log = make_sensor_log(
            {
                "BME280": {"humidity": 39.55},
                "SCD30": {"relative_humidity": 39.2},
            }
        )
        units = make_sensor_units({"BME280": {"humidity": "%"}, "SCD30": {"relative_humidity": "%"}})

        readings = collect_summary_readings(log, units)

        assert set(readings) == {"humidity"}
        assert readings["humidity"]["values"] == [39.55, 39.2]

    def test_first_available_unit_wins(self):
        log = make_sensor_log({"BME280": {"temperature": 29.0}, "SCD30": {"temperature": 30.4}})
        units = make_sensor_units({"SCD30": {"temperature": "C"}})

        readings = collect_summary_readings(log, units)

        assert readings["temperature"]["unit"] == "C"

    def test_measurement_with_no_unit_still_collects_its_value(self):
        log = make_sensor_log({"BME280": {"temperature": 29.0}})
        units = make_sensor_units({})

        readings = collect_summary_readings(log, units)

        assert readings["temperature"]["values"] == [29.0]
        assert readings["temperature"]["unit"] is None

    def test_no_summary_measurements_yields_nothing(self):
        log = make_sensor_log({"PMSA003I": {"pm25_standard": 6}})
        units = make_sensor_units({"PMSA003I": {"pm25_standard": "ug/m3"}})

        assert collect_summary_readings(log, units) == {}


class TestFormatSummaryMeasurementLine:
    def test_single_reading_is_not_labelled_as_an_average(self):
        readings = {"light": {"values": [200.0], "unit": "lx"}}

        assert format_summary_measurement_line("light", readings) == "💡 *Light*: 200 lx"

    def test_multiple_readings_are_averaged_and_labelled(self):
        readings = {"temperature": {"values": [29.0, 30.4], "unit": "C"}}

        assert format_summary_measurement_line("temperature", readings) == "🌡️ *Temperature (avg)*: 29.70 °C"

    def test_missing_measurement_renders_no_line(self):
        assert format_summary_measurement_line("co2", {}) is None

    def test_measurement_present_but_empty_renders_no_line(self):
        readings = {"co2": {"values": [], "unit": "ppm"}}

        assert format_summary_measurement_line("co2", readings) is None


class TestRemoveTrailingDivider:
    def test_trailing_divider_is_dropped(self):
        blocks = [SectionBlock(text="a"), DividerBlock()]

        remove_trailing_divider(blocks)

        assert len(blocks) == 1

    def test_non_divider_tail_is_untouched(self):
        blocks = [DividerBlock(), SectionBlock(text="a")]

        remove_trailing_divider(blocks)

        assert len(blocks) == 2

    def test_empty_list_is_safe(self):
        blocks = []

        remove_trailing_divider(blocks)

        assert blocks == []


class TestSummaryMessageBlocks:
    def test_header_names_the_reporting_device(self):
        """
        The header hardcodes a single device. Pinned deliberately: with a second SMIBHID
        installed this becomes misleading, and issue #510 has to change it.
        """
        log = make_sensor_log({"BME280": {"temperature": 21.0}}, device="SMIBHID-MAIN")
        units = make_sensor_units({"BME280": {"temperature": "C"}})

        blocks = build_sensor_message_blocks(log, units, detailed=False)

        assert "SMIBHID-MAIN" in section_texts(blocks)[0]

    def test_summary_lines_follow_the_declared_summary_order(self):
        log = make_sensor_log(
            {
                "BH1750": {"light": 200.0},
                "BME280": {"temperature": 21.0, "humidity": 40.0},
                "SCD30": {"co2": 480.2},
            }
        )
        units = make_sensor_units(
            {
                "BH1750": {"light": "lx"},
                "BME280": {"temperature": "C", "humidity": "%"},
                "SCD30": {"co2": "ppm"},
            }
        )

        blocks = build_sensor_message_blocks(log, units, detailed=False)
        body = section_texts(blocks)[1]
        positions = [body.index(name) for name in ("Temperature", "Humidity", "Light", "CO₂")]

        assert positions == sorted(positions)
        assert [m for m in SUMMARY_MEASUREMENTS] == ["temperature", "humidity", "light", "co2"]

    def test_summary_excludes_detailed_only_measurements(self):
        log = make_sensor_log(
            {"BME280": {"temperature": 21.0, "pressure": 1013.0}, "PMSA003I": {"pm25_standard": 6}}
        )
        units = make_sensor_units({"BME280": {"temperature": "C", "pressure": "hPa"}})

        rendered = rendered_text(build_sensor_message_blocks(log, units, detailed=False))

        assert "Temperature" in rendered
        assert "Pressure" not in rendered
        assert "PM2.5" not in rendered

    def test_summary_points_at_the_detailed_command(self):
        log = make_sensor_log({"BME280": {"temperature": 21.0}})
        units = make_sensor_units({"BME280": {"temperature": "C"}})

        rendered = rendered_text(build_sensor_message_blocks(log, units, detailed=False))

        assert "/howfresh detailed" in rendered

    def test_no_summary_measurements_still_renders_a_message(self):
        """A particulate-only device must not produce a header with an empty body."""
        log = make_sensor_log({"PMSA003I": {"pm25_standard": 6}})
        units = make_sensor_units({"PMSA003I": {"pm25_standard": "ug/m3"}})

        rendered = rendered_text(build_sensor_message_blocks(log, units, detailed=False))

        assert "No summary sensor readings found." in rendered


class TestDetailedMessageBlocks:
    def test_each_sensor_gets_its_own_labelled_section(self):
        log = make_sensor_log({"BH1750": {"light": 200.0}, "BME280": {"temperature": 21.0}})
        units = make_sensor_units({"BH1750": {"light": "lx"}, "BME280": {"temperature": "C"}})

        rendered = rendered_text(build_sensor_message_blocks(log, units, detailed=True))

        assert "*Light (BH1750)*" in rendered
        assert "*Climate (BME280)*" in rendered

    def test_sensors_are_rendered_in_the_declared_order(self):
        log = make_sensor_log(
            {
                "InternalMetrics": {"relay_on_time": 7200},
                "BME280": {"temperature": 21.0},
                "BH1750": {"light": 200.0},
            }
        )
        units = make_sensor_units({})

        rendered = rendered_text(build_sensor_message_blocks(log, units, detailed=True))
        positions = [rendered.index(label) for label in ("BH1750", "BME280", "Internal Metrics")]

        assert positions == sorted(positions)

    def test_detailed_reports_both_humidity_readings_separately(self):
        """
        Detailed mode keeps the two readings as separate lines under their own sensors, but
        the alias in normalize_measurement_name means SCD30's `relative_humidity` still
        renders with the label "Humidity" - so both lines read identically and are only told
        apart by the sensor heading above them.

        Pinned as-is rather than "fixed": the headings do disambiguate today. It matters for
        issue #510 though, because a merged multi-device table has no per-sensor heading to
        lean on and these row labels would collide.
        """
        log = make_sensor_log(
            {"BME280": {"humidity": 39.55}, "SCD30": {"relative_humidity": 39.2}}
        )
        units = make_sensor_units({"BME280": {"humidity": "%"}, "SCD30": {"relative_humidity": "%"}})

        rendered = rendered_text(build_sensor_message_blocks(log, units, detailed=True))

        assert "*Humidity*: 39.55 %" in rendered
        assert "*Humidity*: 39.20 %" in rendered
        assert rendered.count("💧 *Humidity*") == 2
        assert "Relative Humidity" not in rendered

    def test_detailed_does_not_average_anything(self):
        log = make_sensor_log({"BME280": {"temperature": 29.0}, "SCD30": {"temperature": 30.4}})
        units = make_sensor_units({"BME280": {"temperature": "C"}, "SCD30": {"temperature": "C"}})

        rendered = rendered_text(build_sensor_message_blocks(log, units, detailed=True))

        assert "(avg)" not in rendered
        assert "29 °C" in rendered
        assert "30.40 °C" in rendered

    def test_unknown_sensor_is_rendered_rather_than_dropped(self):
        """A newly added sensor must show up before anyone writes a label mapping for it."""
        log = make_sensor_log({"SGP30": {"tvoc": 120}})
        units = make_sensor_units({"SGP30": {"tvoc": "ppb"}})

        rendered = rendered_text(build_sensor_message_blocks(log, units, detailed=True))

        assert "*SGP30*" in rendered
        assert "*Tvoc*: 120 ppb" in rendered

    def test_message_does_not_end_on_a_divider(self):
        log = make_sensor_log({"BH1750": {"light": 200.0}})
        units = make_sensor_units({"BH1750": {"light": "lx"}})

        blocks = build_sensor_message_blocks(log, units, detailed=True)

        assert not isinstance(blocks[-1], DividerBlock)

    def test_relay_on_time_is_humanized_in_the_detailed_readout(self):
        log = make_sensor_log({"InternalMetrics": {"relay_on_time": 1741003}})
        units = make_sensor_units({"InternalMetrics": {"relay_on_time": "s"}})

        rendered = rendered_text(build_sensor_message_blocks(log, units, detailed=True))

        assert "1741003" not in rendered
        assert "20 days" in rendered


class TestBlocksAreValidSlackPayloads:
    """
    The helpers build slack_sdk block objects that get posted verbatim. A block that fails
    the SDK's own validation would only surface as a Slack API error at command time.
    """

    @pytest.mark.parametrize("detailed", [False, True])
    def test_rendered_blocks_serialize_and_validate(self, detailed):
        log = make_sensor_log(
            {
                "BH1750": {"light": 200.0},
                "BME280": {"temperature": 29.0, "humidity": 39.55, "pressure": 1020.2},
                "SCD30": {"co2": 480.2, "temperature": 30.4, "relative_humidity": 39.2},
                "PMSA003I": {"pm25_standard": 6, "particles_03um": 744},
                "InternalMetrics": {"relay_on_time": 1741003},
            }
        )
        units = make_sensor_units(
            {
                "BH1750": {"light": "lx"},
                "BME280": {"temperature": "C", "humidity": "%", "pressure": "hPa"},
                "SCD30": {"co2": "ppm", "temperature": "C", "relative_humidity": "%"},
                "PMSA003I": {"pm25_standard": "ug/m3", "particles_03um": "count/0.1L"},
                "InternalMetrics": {"relay_on_time": "s"},
            }
        )

        blocks = build_sensor_message_blocks(log, units, detailed=detailed)

        assert blocks
        for block in blocks:
            block.validate_json()

    def test_section_text_stays_within_slack_limit(self):
        """
        Slack truncates section text at 3000 characters. One device's particulate readout is
        already 12 lines; this guards the single-section-per-sensor approach as more sensors
        (and, per #510, more devices) land.
        """
        log = make_sensor_log(
            {
                "PMSA003I": {
                    "pm10_standard": 5, "pm25_standard": 6, "pm100_standard": 6,
                    "pm10_env": 5, "pm25_env": 6, "pm100_env": 6,
                    "particles_03um": 744, "particles_05um": 232, "particles_10um": 30,
                    "particles_25um": 0, "particles_50um": 0, "particles_100um": 0,
                }
            }
        )
        units = make_sensor_units({})

        blocks = build_sensor_message_blocks(log, units, detailed=True)

        for text in section_texts(blocks):
            assert len(text) <= 3000
