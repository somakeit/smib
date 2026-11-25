"""
Unit tests for the relay on-time accounting in plugins.space.relaystate.common.

These cover the pure calculation helpers (_apply_transition, _live_since_reset,
observed_divergence) and the bootstrap baseline seeding. They deliberately avoid the DB:
record_relay_state_report and friends are find-then-save coroutines, whereas every bug these
tests pin down was an arithmetic/baseline bug reachable without Mongo.

Background - S.M.I.B.H.I.D. is authoritative for on-time: it counts continuously from its own
checkpoints, persists them before pushing, and can be seeded directly when on-time needs
backfilling after a filter change. SMIB keeps an independent computed figure purely to
cross-check that counter, and never overwrites either side.

The live SMIBHID-FAN record had its two reset baselines left skewed (computed side 0, reported
side a device lifetime counter) by a delete-and-reseed while the relay was on, which made
"since reset" mean a since-reset figure on one branch and a lifetime figure on the other.
"""

from datetime import UTC, datetime, timedelta

import pytest

from plugins.space.relaystate.common import (
    _apply_transition,
    _live_since_reset,
    observed_divergence,
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

    def test_very_long_session_is_credited_in_full(self):
        """
        No upper bound on a session. An earlier version discarded sessions over a week as
        implausible, which would also have discarded a legitimately long run - and the
        divergence it was built to prevent turned out to be a deliberate device-side seed,
        not corruption.
        """
        duration = timedelta(days=20, hours=4).total_seconds()
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

    def test_long_open_session_is_not_capped(self):
        """
        A long session must be reported at full length - capping it would mask exactly the
        disagreement the drift alert exists to surface.
        """
        age = timedelta(days=400).total_seconds()
        relay_state = make_relay_state(
            computed_total_active_seconds=0.0,
            computed_total_active_seconds_at_last_reset=0.0,
            active_since=T0 - timedelta(seconds=age),
        )

        assert _live_since_reset(relay_state, T0) == pytest.approx(age)

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

    def test_device_side_seed_leaves_smib_computing_from_zero(self):
        """
        A device first seen mid-life (e.g. its counter seeded after a filter change) must leave
        SMIB computing its own figure from zero, with both reset baselines agreeing, so the
        two sides are comparable from the first event rather than being silently conflated.
        """
        seeded_lifetime = 1740883.0
        session_seconds = 3159.0

        relay_state = make_relay_state(
            reported_total_active_seconds=seeded_lifetime,
            reported_total_active_seconds_at_last_reset=seeded_lifetime,
        )

        _apply_transition(relay_state, make_report(active=True), T0)
        relay_state.active = True

        off_at = T0 + timedelta(seconds=session_seconds)
        _apply_transition(relay_state, make_report(active=False, timestamp=off_at), off_at)
        relay_state.active = False
        relay_state.reported_total_active_seconds = seeded_lifetime + session_seconds

        # SMIB only ever saw the one session, and the device agrees on that increment.
        assert relay_state.computed_total_active_seconds == pytest.approx(session_seconds)
        assert observed_divergence(relay_state, off_at) == pytest.approx(0.0)


class TestLifetimeAlertUsesAuthoritativeCounter:
    """
    The relay-lifetime decision ("has the filter done its hours?") must be made on
    S.M.I.B.H.I.D.'s reported counter, not SMIB's inferred one. SMIB's figure can be skewed by
    a single lost transition, and on a device whose counter was seeded after a filter change
    the two differ by the whole backfill - alerting on the wrong one would be badly misleading.
    """

    def test_authoritative_and_computed_can_disagree_on_threshold(self):
        """
        A device seeded with backfill: the device says the threshold is passed, SMIB's own
        figure says nowhere near. Only the device's view should decide.
        """
        threshold = timedelta(days=30).total_seconds()
        seeded = timedelta(days=29).total_seconds()

        relay_state = make_relay_state(
            active=False,
            active_since=None,
            computed_total_active_seconds=timedelta(days=2).total_seconds(),
            computed_total_active_seconds_at_last_reset=0.0,
            reported_total_active_seconds=seeded + timedelta(days=2).total_seconds(),
            reported_total_active_seconds_at_last_reset=0.0,
        )

        reported_since_reset = (
            relay_state.reported_total_active_seconds
            - relay_state.reported_total_active_seconds_at_last_reset
        )
        computed_since_reset = (
            relay_state.computed_total_active_seconds
            - relay_state.computed_total_active_seconds_at_last_reset
        )

        assert reported_since_reset >= threshold
        assert computed_since_reset < threshold
        # The divergence is reported rather than hidden, so the disagreement is investigable.
        assert observed_divergence(relay_state, T0) == pytest.approx(-seeded)


class TestLastReportAtExtrapolation:
    """
    The reported counter only advances when a report lands, and the value it carries already
    includes on-time up to *that report*. So between reports it is stale by the time since the
    last report - not by the length of the session, which would double-count.
    """

    def test_reported_counter_is_current_as_of_the_last_report(self):
        """
        Mirrors the live record: a session opened at 16:49:35 and a report at 20:07:35 whose
        counter already covers the intervening 3h18m. Extrapolating from active_since would
        add that span a second time.
        """
        session_start = datetime(2026, 11, 25, 16, 49, 35, tzinfo=UTC)
        last_report = datetime(2026, 11, 25, 20, 7, 35, tzinfo=UTC)
        now = last_report + timedelta(minutes=10)

        relay_state = make_relay_state(
            active=True,
            active_since=session_start,
            last_report_at=last_report,
            reported_total_active_seconds=5128175.0,
            reported_total_active_seconds_at_last_reset=0.0,
        )

        from_last_report = (now - relay_state.last_report_at).total_seconds()
        from_active_since = (now - relay_state.active_since).total_seconds()

        assert from_last_report == pytest.approx(600.0)
        # Extrapolating from active_since would add ~3.3h of already-counted time.
        assert from_active_since - from_last_report == pytest.approx(11880.0)
