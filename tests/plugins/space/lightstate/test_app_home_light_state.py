"""
Unit tests for the App Home light state blocks in plugins.space.lightstate.app_home.

These cover the device selection, staleness and rendering helpers. They avoid the DB: the
block builders take SpaceLightState documents and return blocks, so the whole render is
reachable without Mongo.

Context - the App Home called SpaceLightState.get_latest_state(), which returns whichever
device saved most recently, so with several S.M.I.B.H.I.D.s the App Home spoke for the whole
space on the word of one arbitrary device. Locally it reported SMIBHID-SPARE, a unit that had
been silent for nine days, because `updated_at` is refreshed on every save and a backfilled
report outranked the live devices. See https://github.com/somakeit/smib/issues/510.
"""

from datetime import UTC, datetime, timedelta

import pytest
from slack_sdk.models.blocks import SectionBlock

from plugins.space.lightstate.app_home import (
    STALE_MARKER,
    build_device_line,
    describe_light_state,
    is_excluded,
    is_stale,
    reading_age,
    select_states_to_render,
)
from plugins.space.lightstate.models import SpaceLightState
from plugins.space.smibhid.config import SmibhidDeviceConfig, config


def make_light_state(
    *,
    device: str = "SMIBHID-FAN",
    light_state: bool = False,
    light_value_lux: float = 120.0,
    threshold_lux: float = 500.0,
    updated_at: datetime | None = None,
) -> SpaceLightState:
    """
    model_construct is used deliberately - SpaceLightState is a Beanie Document, and normal
    instantiation requires an initialised Mongo collection. The helpers under test only read
    plain attributes.
    """
    return SpaceLightState.model_construct(
        device=device,
        light_state=light_state,
        light_value_lux=light_value_lux,
        threshold_lux=threshold_lux,
        updated_at=updated_at or datetime.now(UTC) - timedelta(minutes=2),
    )


class TestReadingAge:
    def test_prefers_the_device_observation_over_the_write_time(self):
        """
        The crux of the original failure: `updated_at` says when SMIB wrote the document, so
        a device that reconnects after a week and pushes once looks instantly fresh. The
        sensor log timestamp is the honest clock.
        """
        state = make_light_state(updated_at=datetime.now(UTC))
        observed_at = datetime.now(UTC) - timedelta(days=9)

        assert reading_age(state, observed_at) > timedelta(days=8)

    def test_falls_back_to_updated_at_without_an_observation(self):
        state = make_light_state(updated_at=datetime.now(UTC) - timedelta(minutes=30))

        assert reading_age(state) >= timedelta(minutes=29)

    def test_handles_a_naive_timestamp_from_mongo(self):
        """MongoDB stores dates without a zone, so a round-tripped document comes back naive."""
        state = make_light_state()
        state.updated_at = (datetime.now(UTC) - timedelta(minutes=10)).replace(tzinfo=None)

        assert reading_age(state) >= timedelta(minutes=9)

    def test_naive_observation_is_also_handled(self):
        state = make_light_state()
        naive_observation = (datetime.now(UTC) - timedelta(days=9)).replace(tzinfo=None)

        assert reading_age(state, naive_observation) > timedelta(days=8)


class TestStaleness:
    def test_recent_reading_is_not_stale(self):
        assert not is_stale(make_light_state())

    def test_old_reading_is_stale(self):
        assert is_stale(make_light_state(updated_at=datetime.now(UTC) - timedelta(hours=6)))

    def test_long_silent_device_is_excluded(self):
        assert is_excluded(make_light_state(updated_at=datetime.now(UTC) - timedelta(days=30)))

    def test_staleness_uses_the_device_observation_when_given(self):
        """A fresh write over a nine-day-old observation must still read as excluded."""
        state = make_light_state(updated_at=datetime.now(UTC))
        observed_at = datetime.now(UTC) - timedelta(days=9)

        assert is_excluded(state, observed_at)


class TestSelectStatesToRender:
    def test_fresh_devices_are_all_kept(self):
        states = [make_light_state(device="SMIBHID-FAN"), make_light_state(device="SMIBHID-WORKSHOP")]

        assert len(select_states_to_render(states)) == 2

    def test_silent_device_is_dropped_while_another_reports(self):
        fresh = make_light_state(device="SMIBHID-FAN")
        silent = make_light_state(device="SMIBHID-SPARE", updated_at=datetime.now(UTC) - timedelta(days=30))

        assert select_states_to_render([fresh, silent]) == [fresh]

    def test_device_silent_by_observation_is_dropped_despite_a_fresh_write(self):
        """The exact live failure: a backfilled report made a dead device look current."""
        fresh = make_light_state(device="SMIBHID-FAN")
        backfilled = make_light_state(device="SMIBHID-SPARE", updated_at=datetime.now(UTC))

        selected = select_states_to_render(
            [fresh, backfilled],
            {"SMIBHID-SPARE": datetime.now(UTC) - timedelta(days=9)},
        )

        assert [state.device for state in selected] == ["SMIBHID-FAN"]

    def test_all_silent_devices_are_all_kept(self):
        """A stale answer beats claiming the light state is unknown when a reading exists."""
        states = [
            make_light_state(device=device, updated_at=datetime.now(UTC) - timedelta(days=30))
            for device in ("SMIBHID-FAN", "SMIBHID-WORKSHOP")
        ]

        assert len(select_states_to_render(states)) == 2

    def test_devices_are_ordered_by_the_shared_device_config(self, monkeypatch):
        monkeypatch.setitem(config.device, "smibhid_workshop", SmibhidDeviceConfig(order=1))
        monkeypatch.setitem(config.device, "smibhid_fan", SmibhidDeviceConfig(order=2))

        states = [make_light_state(device="SMIBHID-FAN"), make_light_state(device="SMIBHID-WORKSHOP")]

        selected = select_states_to_render(states)

        assert [state.device for state in selected] == ["SMIBHID-WORKSHOP", "SMIBHID-FAN"]

    def test_ordering_is_independent_of_input_order(self):
        forwards = select_states_to_render(
            [make_light_state(device="SMIBHID-FAN"), make_light_state(device="SMIBHID-WORKSHOP")]
        )
        backwards = select_states_to_render(
            [make_light_state(device="SMIBHID-WORKSHOP"), make_light_state(device="SMIBHID-FAN")]
        )

        assert [s.device for s in forwards] == [s.device for s in backwards]


class TestDescribeLightState:
    def test_lights_on(self):
        assert "*on*" in describe_light_state(make_light_state(light_state=True))

    def test_lights_off(self):
        assert "*off*" in describe_light_state(make_light_state(light_state=False))


class TestBuildDeviceLine:
    def test_line_uses_the_shared_friendly_name(self, monkeypatch):
        monkeypatch.setitem(config.device, "smibhid_fan", SmibhidDeviceConfig(name="Clean Room"))

        line = build_device_line(make_light_state(device="SMIBHID-FAN"), None)

        assert "Clean Room" in line
        assert "SMIBHID-FAN" not in line

    def test_line_falls_back_to_the_hostname(self):
        line = build_device_line(make_light_state(device="SMIBHID-UNCONFIGURED"), None)

        assert "SMIBHID-UNCONFIGURED" in line

    def test_stale_line_is_marked(self):
        state = make_light_state(updated_at=datetime.now(UTC) - timedelta(hours=6))

        assert STALE_MARKER in build_device_line(state, None)

    def test_fresh_line_is_not_marked(self):
        assert STALE_MARKER not in build_device_line(make_light_state(), None)

    def test_line_reports_the_measured_time_not_the_write_time(self):
        """A backfilled write must not make a nine-day-old reading read as recent."""
        state = make_light_state(updated_at=datetime.now(UTC))

        line = build_device_line(state, datetime.now(UTC) - timedelta(days=9))

        assert "days ago" in line

    def test_line_includes_the_level_and_threshold(self):
        line = build_device_line(make_light_state(light_value_lux=23.57, threshold_lux=500.0), None)

        assert "23.57 lx" in line
        assert "500.00 lx" in line
