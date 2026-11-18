"""
Unit tests for the relay on-time accounting in plugins.space.relaystate.common.

These cover the pure calculation helpers (_apply_transition, _live_since_reset,
_reconcile_with_reported) and the bootstrap baseline seeding. They deliberately avoid the DB:
record_relay_state_report and friends are find-then-save coroutines, whereas every bug these
tests pin down was an arithmetic/baseline bug reachable without Mongo.

Background - the live SMIBHID-FAN record on smib-pi accumulated ~20 days of phantom on-time
in a single OFF transition because an older schema's document was loaded with active=True
but no usable active_since, and the resulting absurd session duration was added straight to
the authoritative total. The reset baselines were also left skewed (computed side 0,
reported side a device lifetime counter), making since_reset mean two different things.
"""

from datetime import UTC, datetime, timedelta

import pytest

from plugins.space.relaystate.common import (
    _apply_transition,
    _live_since_reset,
    _reconcile_with_reported,
)
from plugins.space.relaystate.config import config
from plugins.space.relaystate.models import RelayState, RelayStateReport

T0 = datetime(2026, 9, 9, 19, 41, 11, tzinfo=UTC)


def make_relay_state(**overrides) -> RelayState:
    """
    A RelayState as the bootstrap path builds it: off, nothing accumulated.

    model_construct is used deliberately - RelayState is a Beanie Document, and normal
    instantiation requires an initialized Mongo collection. The helpers under test only
    read and write plain attributes, so a constructed model exercises them faithfully
    without standing up a database.
    """
    defaults = dict(
        device="SMIBHID-TEST",
        active=False,
        reported_total_active_seconds=0.0,
        reported_total_active_seconds_at_last_reset=0.0,
        computed_total_active_seconds=0.0,
        computed_total_active_seconds_at_last_reset=0.0,
        active_since=None,
    )
    return RelayState.model_construct(**{**defaults, **overrides})


def make_report(active: bool, total_active_seconds: float = 0.0, timestamp: datetime = T0) -> RelayStateReport:
    return RelayStateReport(
        active=active,
        total_active_seconds=total_active_seconds,
        timestamp=timestamp,
    )


class TestApplyTransitionHappyPath:
    def test_off_to_on_opens_session_without_crediting_time(self):
        relay_state = make_relay_state(active=False)

        _apply_transition(relay_state, make_report(active=True), T0)

        assert relay_state.active_since == T0
        assert relay_state.computed_total_active_seconds == 0.0

    def test_on_to_off_credits_exactly_the_session_duration(self):
        relay_state = make_relay_state(active=True, active_since=T0)
        off_at = T0 + timedelta(minutes=52, seconds=39)

        _apply_transition(relay_state, make_report(active=False, timestamp=off_at), off_at)

        assert relay_state.computed_total_active_seconds == pytest.approx(3159.0)
        assert relay_state.active_since is None

    def test_on_to_on_heartbeat_does_not_double_credit(self):
        """SMIBHID heartbeats hourly while ON; only the OFF transition may credit time."""
        relay_state = make_relay_state(active=True, active_since=T0)

        for hours in (1, 2, 3):
            _apply_transition(relay_state, make_report(active=True), T0 + timedelta(hours=hours))

        assert relay_state.computed_total_active_seconds == 0.0
        assert relay_state.active_since == T0

    def test_repeated_sessions_accumulate(self):
        relay_state = make_relay_state(active=False)
        cursor = T0

        for _ in range(3):
            _apply_transition(relay_state, make_report(active=True), cursor)
            relay_state.active = True
            cursor += timedelta(hours=2)
            _apply_transition(relay_state, make_report(active=False), cursor)
            relay_state.active = False
            cursor += timedelta(hours=1)

        assert relay_state.computed_total_active_seconds == pytest.approx(3 * 7200.0)

    def test_off_to_off_with_no_open_session_is_a_noop(self):
        relay_state = make_relay_state(active=False, active_since=None)

        _apply_transition(relay_state, make_report(active=False), T0)

        assert relay_state.computed_total_active_seconds == 0.0
        assert relay_state.active_since is None


class TestApplyTransitionRejectsBadDurations:
    def test_out_of_order_timestamp_is_clamped_to_zero(self):
        relay_state = make_relay_state(active=True, active_since=T0)
        earlier = T0 - timedelta(minutes=5)

        _apply_transition(relay_state, make_report(active=False, timestamp=earlier), earlier)

        assert relay_state.computed_total_active_seconds == 0.0
        assert relay_state.active_since is None

    def test_implausibly_long_session_is_discarded_not_credited(self):
        """
        Regression: the live SMIBHID-FAN record gained 1744042s (~20.2 days) in one OFF
        transition from a stale active_since. Such a session must be dropped, not banked.
        """
        stale_active_since = T0 - timedelta(days=20, hours=4)
        relay_state = make_relay_state(active=True, active_since=stale_active_since)

        _apply_transition(relay_state, make_report(active=False), T0)

        assert relay_state.computed_total_active_seconds == 0.0
        assert relay_state.active_since is None

    def test_session_just_under_the_cap_is_still_credited(self):
        """The guard must not silently eat legitimate long sessions."""
        duration = config.max_plausible_on_session_seconds - 60
        relay_state = make_relay_state(active=True, active_since=T0)
        off_at = T0 + timedelta(seconds=duration)

        _apply_transition(relay_state, make_report(active=False, timestamp=off_at), off_at)

        assert relay_state.computed_total_active_seconds == pytest.approx(duration)

    def test_off_transition_with_no_active_since_credits_nothing(self):
        """active=True with active_since=None is the older-schema shape - must not guess."""
        relay_state = make_relay_state(active=True, active_since=None)

        _apply_transition(relay_state, make_report(active=False), T0)

        assert relay_state.computed_total_active_seconds == 0.0

    def test_computed_total_never_goes_negative(self):
        relay_state = make_relay_state(active=True, active_since=T0 + timedelta(days=1))

        _apply_transition(relay_state, make_report(active=False), T0)

        assert relay_state.computed_total_active_seconds >= 0.0


class TestLiveSinceReset:
    def test_closed_session_is_just_the_reset_delta(self):
        relay_state = make_relay_state(
            computed_total_active_seconds=5000.0,
            computed_total_active_seconds_at_last_reset=2000.0,
            active_since=None,
        )

        assert _live_since_reset(relay_state, T0) == pytest.approx(3000.0)

    def test_open_session_is_live_adjusted(self):
        """
        Without live adjustment the frozen computed total is compared against a reported
        total that keeps climbing, manufacturing drift that grows across the ON session.
        """
        relay_state = make_relay_state(
            computed_total_active_seconds=5000.0,
            computed_total_active_seconds_at_last_reset=2000.0,
            active_since=T0,
        )

        result = _live_since_reset(relay_state, T0 + timedelta(hours=1))

        assert result == pytest.approx(3000.0 + 3600.0)

    def test_stale_active_since_is_capped(self):
        """A stale active_since must not inflate every periodic drift check without bound."""
        relay_state = make_relay_state(
            computed_total_active_seconds=0.0,
            computed_total_active_seconds_at_last_reset=0.0,
            active_since=T0 - timedelta(days=400),
        )

        result = _live_since_reset(relay_state, T0)

        assert result == pytest.approx(config.max_plausible_on_session_seconds)

    def test_future_active_since_does_not_subtract_time(self):
        relay_state = make_relay_state(
            computed_total_active_seconds=1000.0,
            computed_total_active_seconds_at_last_reset=0.0,
            active_since=T0 + timedelta(hours=5),
        )

        assert _live_since_reset(relay_state, T0) == pytest.approx(1000.0)


class TestBootstrapBaselines:
    """
    The bootstrap must seed both reset baselines consistently. Seeding only the reported side
    (as the live record was) leaves the computed branch measuring lifetime on-time while the
    reported branch measures since-reset on-time, breaking drift and the lifetime alert.
    """

    def test_both_reset_baselines_are_consistent_at_bootstrap(self):
        device_lifetime = 1740883.0
        relay_state = make_relay_state(
            reported_total_active_seconds=device_lifetime,
            reported_total_active_seconds_at_last_reset=device_lifetime,
        )

        computed_since_reset = (
            relay_state.computed_total_active_seconds
            - relay_state.computed_total_active_seconds_at_last_reset
        )
        reported_since_reset = (
            relay_state.reported_total_active_seconds
            - relay_state.reported_total_active_seconds_at_last_reset
        )

        assert computed_since_reset == 0.0
        assert reported_since_reset == 0.0

    def test_first_session_keeps_both_sides_in_step(self):
        """
        End-to-end on the arithmetic only: a device first seen mid-life, then one real
        session, must show equal computed and reported since-reset deltas (i.e. zero drift).
        """
        device_lifetime = 1740883.0
        session_seconds = 3159.0

        relay_state = make_relay_state(
            reported_total_active_seconds=device_lifetime,
            reported_total_active_seconds_at_last_reset=device_lifetime,
        )

        _apply_transition(relay_state, make_report(active=True), T0)
        relay_state.active = True

        off_at = T0 + timedelta(seconds=session_seconds)
        _apply_transition(relay_state, make_report(active=False, timestamp=off_at), off_at)
        relay_state.active = False
        relay_state.reported_total_active_seconds = device_lifetime + session_seconds

        computed_since_reset = (
            relay_state.computed_total_active_seconds
            - relay_state.computed_total_active_seconds_at_last_reset
        )
        reported_since_reset = (
            relay_state.reported_total_active_seconds
            - relay_state.reported_total_active_seconds_at_last_reset
        )

        assert computed_since_reset == pytest.approx(session_seconds)
        assert reported_since_reset == pytest.approx(session_seconds)
        drift = abs(computed_since_reset - reported_since_reset)
        assert drift <= config.total_active_seconds_drift_warning_threshold_seconds

    def test_legacy_shaped_record_does_not_bank_phantom_on_time(self):
        """
        Regression for the live failure: a record carrying active=True from an older schema,
        with computed_total_active_seconds=0 and a long-stale active_since, must not turn its
        first OFF transition into weeks of authoritative on-time.
        """
        relay_state = make_relay_state(
            active=True,
            active_since=T0 - timedelta(days=20, hours=4),
            computed_total_active_seconds=0.0,
            reported_total_active_seconds=1740883.0,
            reported_total_active_seconds_at_last_reset=0.0,
        )

        _apply_transition(relay_state, make_report(active=False), T0)

        assert relay_state.computed_total_active_seconds < timedelta(days=1).total_seconds()


class TestReconcileWithReported:
    """
    SMIBHID counts on-time continuously and persists each checkpoint before pushing, so its
    counter survives a dropped report. SMIB only infers state between the reports it gets, so
    a lost transition skews the computed total in one direction or the other - miss an OFF and
    SMIB credits the whole gap as ON, miss an ON and it credits none of it. The live
    SMIBHID-FAN record wandered by +/-1-3 hours this way, in near-exact 3600s steps matching
    the hourly heartbeat. Reconciliation takes the correction the device already sends.
    """

    def test_snaps_computed_up_to_reported_when_smib_under_counted(self):
        """Lost ON transition: SMIBHID counted the hour, SMIB credited none of it."""
        relay_state = make_relay_state(
            active=False,
            active_since=None,
            computed_total_active_seconds=10000.0,
            reported_total_active_seconds_at_last_reset=0.0,
        )

        correction = _reconcile_with_reported(relay_state, make_report(active=False, total_active_seconds=13600.0))

        assert correction == pytest.approx(3600.0)
        assert relay_state.computed_total_active_seconds == pytest.approx(13600.0)

    def test_snaps_computed_down_to_reported_when_smib_over_counted(self):
        """Lost OFF transition: SMIB credited the whole gap as ON, SMIBHID did not."""
        relay_state = make_relay_state(
            active=False,
            active_since=None,
            computed_total_active_seconds=13600.0,
            reported_total_active_seconds_at_last_reset=0.0,
        )

        correction = _reconcile_with_reported(relay_state, make_report(active=False, total_active_seconds=10000.0))

        assert correction == pytest.approx(-3600.0)
        assert relay_state.computed_total_active_seconds == pytest.approx(10000.0)

    def test_respects_the_reset_baselines(self):
        """Both sides must be compared since their own reset point, not as lifetime totals."""
        relay_state = make_relay_state(
            active=False,
            active_since=None,
            computed_total_active_seconds=5000.0,
            computed_total_active_seconds_at_last_reset=2000.0,
            reported_total_active_seconds_at_last_reset=1740883.0,
        )

        # reported_since_reset = 1746483 - 1740883 = 5600; computed_since_reset = 3000
        correction = _reconcile_with_reported(relay_state, make_report(active=False, total_active_seconds=1746483.0))

        assert correction == pytest.approx(2600.0)
        assert relay_state.computed_total_active_seconds == pytest.approx(7600.0)

    def test_noop_while_relay_is_on(self):
        """An in-flight session legitimately isn't banked yet - that is not drift."""
        relay_state = make_relay_state(
            active=True,
            active_since=T0,
            computed_total_active_seconds=10000.0,
            reported_total_active_seconds_at_last_reset=0.0,
        )

        correction = _reconcile_with_reported(relay_state, make_report(active=True, total_active_seconds=13600.0))

        assert correction is None
        assert relay_state.computed_total_active_seconds == pytest.approx(10000.0)

    def test_noop_when_off_report_still_has_an_open_session(self):
        relay_state = make_relay_state(
            active=False,
            active_since=T0,
            computed_total_active_seconds=10000.0,
            reported_total_active_seconds_at_last_reset=0.0,
        )

        assert _reconcile_with_reported(relay_state, make_report(active=False, total_active_seconds=13600.0)) is None

    def test_noop_within_tolerance(self):
        """Sub-report jitter must not churn the authoritative total on every heartbeat."""
        relay_state = make_relay_state(
            active=False,
            active_since=None,
            computed_total_active_seconds=10000.0,
            reported_total_active_seconds_at_last_reset=0.0,
        )
        within = config.reconcile_tolerance_seconds / 2

        correction = _reconcile_with_reported(
            relay_state, make_report(active=False, total_active_seconds=10000.0 + within)
        )

        assert correction is None
        assert relay_state.computed_total_active_seconds == pytest.approx(10000.0)

    def test_refuses_correction_beyond_a_plausible_session(self):
        """
        A huge gap means the two sides aren't describing the same window (mismatched
        baselines, a one-sided reset, a reused hostname) - importing it would corrupt the
        total, so leave it for the drift alert.
        """
        relay_state = make_relay_state(
            active=False,
            active_since=None,
            computed_total_active_seconds=10000.0,
            reported_total_active_seconds_at_last_reset=0.0,
        )
        absurd = 10000.0 + config.max_plausible_on_session_seconds * 2

        correction = _reconcile_with_reported(relay_state, make_report(active=False, total_active_seconds=absurd))

        assert correction is None
        assert relay_state.computed_total_active_seconds == pytest.approx(10000.0)

    def test_never_drives_computed_total_negative(self):
        relay_state = make_relay_state(
            active=False,
            active_since=None,
            computed_total_active_seconds=100.0,
            computed_total_active_seconds_at_last_reset=0.0,
            reported_total_active_seconds_at_last_reset=5000.0,
        )

        # reported_since_reset = 0 - 5000 = -5000, which would take computed below zero.
        correction = _reconcile_with_reported(relay_state, make_report(active=False, total_active_seconds=0.0))

        assert correction is None
        assert relay_state.computed_total_active_seconds >= 0.0

    def test_repeated_reports_converge_and_then_settle(self):
        """After one correction the next identical report must be a no-op, not oscillate."""
        relay_state = make_relay_state(
            active=False,
            active_since=None,
            computed_total_active_seconds=10000.0,
            reported_total_active_seconds_at_last_reset=0.0,
        )
        report = make_report(active=False, total_active_seconds=13600.0)

        first = _reconcile_with_reported(relay_state, report)
        second = _reconcile_with_reported(relay_state, report)

        assert first == pytest.approx(3600.0)
        assert second is None
        assert relay_state.computed_total_active_seconds == pytest.approx(13600.0)
