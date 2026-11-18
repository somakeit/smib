"""
Unit tests for the relay on-time replay in scripts/repair_relay_on_time.py.

The replay rewrites the authoritative total on a live record, so its arithmetic needs the
same scrutiny as the plugin's. These tests drive `replay` directly with synthetic event
streams - no DB, no network.
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from plugins.space.relaystate.config import config  # noqa: E402
from plugins.space.relaystate.models import RelayResetHistory, RelayStateHistory  # noqa: E402
from repair_relay_on_time import replay, resolve_reported_baseline  # noqa: E402

T0 = datetime(2026, 9, 9, 19, 41, 11, tzinfo=UTC)


def event(active: bool, offset_seconds: float, reported: float = 0.0) -> RelayStateHistory:
    return RelayStateHistory.model_construct(
        device="SMIBHID-TEST",
        timestamp=T0 + timedelta(seconds=offset_seconds),
        received_at=T0 + timedelta(seconds=offset_seconds),
        active=active,
        reported_total_active_seconds=reported,
        computed_total_active_seconds=0.0,
    )


def healthy_stream(*transitions: tuple[bool, float]) -> list[RelayStateHistory]:
    """
    Build an event stream whose reported counter tracks real on-time, as a device with no
    lost pushes would report it.

    The replay now runs the production reconciliation, which treats the reported counter as
    the better figure - so a stream where that counter is flat while the relay cycles is a
    *device that lost pushes*, not a neutral fixture. Tests of the transition arithmetic need
    a self-consistent stream, or reconciliation correctly snaps the total to the stub value.
    """
    events: list[RelayStateHistory] = []
    reported = 0.0
    active = False
    since: float | None = None

    for is_on, offset in transitions:
        if is_on and not active:
            since = offset
        elif not is_on and active and since is not None:
            reported += offset - since
            since = None
        elif is_on and active and since is not None:
            # Heartbeat mid-session: the device credits elapsed time continuously.
            reported += offset - since
            since = offset
        active = is_on
        events.append(event(is_on, offset, reported=reported))

    return events


def reset(offset_seconds: float, previous_total: float = 0.0) -> RelayResetHistory:
    return RelayResetHistory.model_construct(
        device="SMIBHID-TEST",
        timestamp=T0 + timedelta(seconds=offset_seconds),
        received_at=T0 + timedelta(seconds=offset_seconds),
        previous_total_active_seconds=previous_total,
        computed_total_active_seconds_at_reset=0.0,
    )


class TestReplayBasics:
    def test_empty_history_yields_zero(self):
        result = replay([], [])

        assert result.computed_total_active_seconds == 0.0
        assert result.events_replayed == 0

    def test_single_session_is_credited_once(self):
        events = healthy_stream((True, 0), (False, 3159))

        result = replay(events, [])

        assert result.computed_total_active_seconds == pytest.approx(3159.0)
        assert result.sessions_credited == 1
        assert result.active is False
        assert result.active_since is None

    def test_multiple_sessions_accumulate(self):
        events = healthy_stream(
            (True, 0), (False, 100),
            (True, 200), (False, 350),
            (True, 400), (False, 410),
        )

        result = replay(events, [])

        assert result.computed_total_active_seconds == pytest.approx(100 + 150 + 10)
        assert result.sessions_credited == 3

    def test_heartbeats_while_on_do_not_double_credit(self):
        """SMIBHID reports hourly while ON; only the closing OFF may credit the session."""
        events = healthy_stream((True, 0), (True, 3600), (True, 7200), (False, 10800))

        result = replay(events, [])

        assert result.computed_total_active_seconds == pytest.approx(10800.0)
        assert result.sessions_credited == 1

    def test_events_are_replayed_in_timestamp_order(self):
        ordered = healthy_stream((True, 0), (False, 600))
        shuffled = [ordered[1], ordered[0]]

        assert replay(shuffled, []).computed_total_active_seconds == pytest.approx(600.0)

    def test_open_session_is_left_open(self):
        """A device currently ON must keep active_since so live adjustment still works."""
        events = healthy_stream((True, 0), (False, 600), (True, 1200))

        result = replay(events, [])

        assert result.computed_total_active_seconds == pytest.approx(600.0)
        assert result.active is True
        assert result.active_since == T0 + timedelta(seconds=1200)

    def test_trailing_off_without_open_session_credits_nothing(self):
        result = replay([event(False, 0), event(False, 600)], [])

        assert result.computed_total_active_seconds == 0.0


class TestReplayQuarantinesCorruption:
    def test_implausible_session_is_rejected_not_banked(self):
        """
        The original failure: a legacy record's first OFF transition implied ~20.2 days of
        on-time. The replay must discard it, otherwise it just reproduces the bad total.
        """
        phantom = timedelta(days=20, hours=4).total_seconds()
        # The device only ever counted the legitimate 1h session - the phantom span comes from
        # SMIB's side (a stale active_since), which is why the reported counter never saw it.
        events = [
            event(True, 0, reported=0.0),
            event(False, phantom, reported=0.0),
            event(True, phantom + 60, reported=0.0),
            event(False, phantom + 3660, reported=3600.0),
        ]

        result = replay(events, [])

        assert result.sessions_rejected == 1
        assert result.rejected_seconds == pytest.approx(phantom)
        # Only the legitimate 1h session survives.
        assert result.computed_total_active_seconds == pytest.approx(3600.0)

    def test_out_of_order_timestamps_credit_zero(self):
        on = event(True, 1000)
        off = event(False, 1000)
        off.timestamp = T0 + timedelta(seconds=500)

        result = replay([on, off], [])

        assert result.computed_total_active_seconds == 0.0

    def test_session_just_under_cap_is_still_credited(self):
        duration = config.max_plausible_on_session_seconds - 60
        events = healthy_stream((True, 0), (False, duration))

        result = replay(events, [])

        assert result.computed_total_active_seconds == pytest.approx(duration)
        assert result.sessions_rejected == 0


class TestReplayHandlesResets:
    def test_reset_rebaselines_without_losing_lifetime_total(self):
        # The device zeroes its counter at the reset, so post-reset readings restart from 0.
        events = [
            event(True, 0, reported=0.0),
            event(False, 600, reported=600.0),
            event(True, 2000, reported=0.0),
            event(False, 2600, reported=600.0),
        ]

        result = replay(events, [reset(1000)])

        assert result.computed_total_active_seconds == pytest.approx(1200.0)
        assert result.computed_total_active_seconds_at_last_reset == pytest.approx(600.0)

    def test_reset_during_open_session_splits_it(self):
        """A reset mid-session banks the pre-reset portion and restarts the session there."""
        events = [event(True, 0, reported=0.0), event(False, 1000, reported=600.0)]

        result = replay(events, [reset(400)])

        assert result.computed_total_active_seconds == pytest.approx(1000.0)
        assert result.computed_total_active_seconds_at_last_reset == pytest.approx(400.0)

    def test_since_reset_is_measured_from_the_reset_point(self):
        events = [
            event(True, 0, reported=0.0),
            event(False, 600, reported=600.0),
            event(True, 1000, reported=0.0),
            event(False, 1600, reported=600.0),
        ]

        result = replay(events, [reset(800)])
        since_reset = (
            result.computed_total_active_seconds
            - result.computed_total_active_seconds_at_last_reset
        )

        assert since_reset == pytest.approx(600.0)

    def test_reset_after_final_event_rebaselines_to_full_total(self):
        events = healthy_stream((True, 0), (False, 600))

        result = replay(events, [reset(5000)])

        assert result.computed_total_active_seconds_at_last_reset == pytest.approx(600.0)
        assert result.resets_applied == 1

    def test_reported_baseline_is_first_observed_reading_when_never_reset(self):
        """
        Regression: baselining the reported side at 0 for a never-reset device leaves a
        residual drift equal to the device's whole pre-SMIB lifetime. SMIBHID-FAN was first
        seen at 1740883s, so that - not 0 - is the baseline.
        """
        events = [event(True, 0, reported=1740883.0), event(False, 600, reported=1741483.0)]

        assert resolve_reported_baseline(events, []) == pytest.approx(1740883.0)

    def test_reported_baseline_uses_latest_reset_when_present(self):
        events = [event(True, 0, reported=1000.0), event(False, 600, reported=1600.0)]
        resets = [reset(200, previous_total=1200.0), reset(400, previous_total=1400.0)]

        assert resolve_reported_baseline(events, resets) == pytest.approx(1400.0)

    def test_reported_baseline_ignores_event_order(self):
        events = [event(False, 600, reported=1741483.0), event(True, 0, reported=1740883.0)]

        assert resolve_reported_baseline(events, []) == pytest.approx(1740883.0)

    def test_multiple_resets_use_the_latest_as_baseline(self):
        events = [
            event(True, 0, reported=0.0), event(False, 600, reported=600.0),
            event(True, 1000, reported=0.0), event(False, 1600, reported=600.0),
            event(True, 2000, reported=0.0), event(False, 2600, reported=600.0),
        ]

        result = replay(events, [reset(800), reset(1800)])

        assert result.resets_applied == 2
        assert result.computed_total_active_seconds == pytest.approx(1800.0)
        assert result.computed_total_active_seconds_at_last_reset == pytest.approx(1200.0)


class TestReplayReconciles:
    """
    The replay must reach the same answer as live processing, so it runs the plugin's own
    reconciliation rather than only the transition rules. An earlier version hand-rolled the
    arithmetic and silently diverged by 6676s on the real SMIBHID-FAN history once
    reconciliation landed in the plugin.
    """

    def test_lost_off_transition_is_corrected_down(self):
        """
        SMIB sees ON then OFF an hour later and credits the whole gap, but the device's
        counter never moved - so the device says the relay was off for that hour.
        """
        events = [
            event(True, 0, reported=0.0),
            event(False, 3600, reported=0.0),
        ]

        result = replay(events, [])

        assert result.reconciliations == 1
        assert result.reconciled_seconds == pytest.approx(3600.0)
        assert result.computed_total_active_seconds == pytest.approx(0.0)

    def test_lost_on_transition_is_corrected_up(self):
        """SMIB had the relay recorded off, but the device counted the full hour as on."""
        events = [
            event(False, 0, reported=0.0),
            event(False, 3600, reported=3600.0),
        ]

        result = replay(events, [])

        assert result.reconciliations == 1
        assert result.computed_total_active_seconds == pytest.approx(3600.0)

    def test_healthy_stream_needs_no_reconciliation(self):
        """A device with no lost pushes must not be corrected at all."""
        events = healthy_stream(
            (True, 0), (False, 600),
            (True, 1200), (False, 2400),
            (True, 3000), (False, 3600),
        )

        result = replay(events, [])

        assert result.reconciliations == 0
        assert result.computed_total_active_seconds == pytest.approx(600 + 1200 + 600)

    def test_no_reconciliation_on_the_first_event(self):
        """There is no history to correct yet, matching record_relay_state_report."""
        events = [event(False, 0, reported=99999.0)]

        result = replay(events, [])

        assert result.reconciliations == 0
        assert result.computed_total_active_seconds == pytest.approx(0.0)

    def test_no_reconciliation_while_a_session_is_open(self):
        """An unbanked in-flight session is not drift."""
        events = [
            event(True, 0, reported=0.0),
            event(True, 3600, reported=3600.0),
        ]

        result = replay(events, [])

        assert result.reconciliations == 0
        assert result.active is True

    def test_jitter_within_tolerance_is_not_corrected(self):
        events = healthy_stream((True, 0), (False, 600))
        events[-1].reported_total_active_seconds = 600.0 + config.reconcile_tolerance_seconds / 2

        result = replay(events, [])

        assert result.reconciliations == 0
        assert result.computed_total_active_seconds == pytest.approx(600.0)
