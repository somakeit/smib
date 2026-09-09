import asyncio
import logging
from collections import defaultdict
from datetime import datetime, UTC, timedelta
from typing import NamedTuple

from smib.utilities import get_humanized_time, get_humanized_timedelta
from .config import config
from .models import RelayState, RelayStateHistory, RelayStateReport, RelayResetReport, RelayResetHistory, AlertState
from ..smibhid.common import get_timestamp

logger = logging.getLogger("Space Relay State Plugin - Common")

# Serializes read-modify-write access to a device's RelayState document within this process,
# since record_relay_state_report/record_relay_state_reset/check_relay_state_for_alerts all do a
# find-then-save with no DB-level atomicity.
_device_locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


def _get_device_lock(device: str) -> asyncio.Lock:
    return _device_locks[device]


class DriftAlertInfo(NamedTuple):
    since_reset: float
    reported: float
    delta: float


class RelayReportOutcome(NamedTuple):
    relay_lifetime_alert_since_reset: float | None
    drift_alert: DriftAlertInfo | None


async def get_relay_state_from_db(device: str) -> RelayState | None:
    return await RelayState.find_one(RelayState.device == device)


def _apply_transition(relay_state: RelayState, report: RelayStateReport, event_timestamp: datetime) -> None:
    was_on = relay_state.active
    is_on = report.active

    if is_on and not was_on:
        relay_state.active_since = event_timestamp
    elif not is_on and was_on and relay_state.active_since is not None:
        duration = (event_timestamp - relay_state.active_since).total_seconds()
        if duration < 0:
            logger.warning(
                f"Relay state report for {relay_state.device} has an out-of-order timestamp "
                f"(event_timestamp={event_timestamp} precedes active_since={relay_state.active_since}); "
                f"clamping ON duration to 0 instead of applying a negative value."
            )
            duration = 0.0
        relay_state.computed_total_active_seconds += duration
        relay_state.active_since = None
    elif not is_on and relay_state.active_since is not None:
        # Turning off with a stale/unexpected active_since (e.g. missed the matching ON) - just clear it.
        relay_state.active_since = None


def _should_resend_alert(alert: AlertState, condition_met: bool, resend_interval: timedelta | None, now: datetime) -> bool:
    """ Shared debounce rule for both alert types: fire on first trigger, then again after resend_interval if still active. """
    if not condition_met:
        return False

    first_alert = not alert.active
    resend_alert = (
        alert.active
        and resend_interval is not None
        and alert.last_sent_at is not None
        and (now - alert.last_sent_at) > resend_interval
    )
    return first_alert or resend_alert


def _update_relay_lifetime_alert_state(relay_state: RelayState, since_reset: float) -> bool:
    """ Mutates relay_state.lifetime_alert as a side effect; call exactly once per check cycle. """
    if config.relay_lifetime_warning_threshold is None:
        return False

    condition_met = since_reset >= config.relay_lifetime_warning_threshold.total_seconds()
    if not condition_met:
        return False

    now = datetime.now(UTC)
    should_alert = _should_resend_alert(relay_state.lifetime_alert, condition_met, config.relay_lifetime_alert_resend_interval, now)
    relay_state.lifetime_alert.active = True

    if not should_alert:
        return False

    relay_state.lifetime_alert.last_sent_at = now
    return True


def _update_drift_alert_state(device: str, relay_state: RelayState, since_reset: float, reported_since_reset: float) -> DriftAlertInfo | None:
    """ Mutates relay_state.drift_alert as a side effect; call exactly once per check cycle. """
    delta = abs(since_reset - reported_since_reset)
    condition_met = delta > config.total_active_seconds_drift_warning_threshold_seconds

    if condition_met:
        logger.warning(
            f"Relay state total_active_seconds drift for {device} exceeds threshold "
            f"({config.total_active_seconds_drift_warning_threshold_seconds}s): "
            f"computed_since_reset={since_reset}s, "
            f"reported_since_reset={reported_since_reset}s, delta={delta}s"
        )

    now = datetime.now(UTC)
    should_alert = _should_resend_alert(relay_state.drift_alert, condition_met, config.drift_warning_alert_resend_interval, now)
    relay_state.drift_alert.active = condition_met

    if not should_alert:
        return None

    relay_state.drift_alert.last_sent_at = now
    return DriftAlertInfo(since_reset=since_reset, reported=reported_since_reset, delta=delta)


def build_relay_lifetime_alert_message(since_reset: float, device: str) -> str:
    return config.relay_lifetime_alert_message_template.format(
        relay_name=config.relay_name,
        device=device,
        duration=get_humanized_timedelta(timedelta(seconds=since_reset)),
        threshold=get_humanized_timedelta(config.relay_lifetime_warning_threshold),
    )


def build_drift_alert_message(device: str, drift: DriftAlertInfo) -> str:
    return (
        f":warning: Relay state total_active_seconds drift for {device} exceeds threshold "
        f"({get_humanized_timedelta(timedelta(seconds=config.total_active_seconds_drift_warning_threshold_seconds))}): "
        f"computed_since_reset={get_humanized_timedelta(timedelta(seconds=drift.since_reset))}, "
        f"reported={get_humanized_timedelta(timedelta(seconds=drift.reported))}, "
        f"delta={get_humanized_timedelta(timedelta(seconds=drift.delta))}"
    )


async def record_relay_state_report(report: RelayStateReport, device: str) -> RelayReportOutcome:
    event_timestamp = get_timestamp(report.timestamp)

    async with _get_device_lock(device):
        relay_state = await get_relay_state_from_db(device)
        is_first_event = relay_state is None

        if relay_state is None:
            # Bootstrap with an "off, unset" baseline so the transition logic below
            # runs uniformly - e.g. a first report of active=True still opens
            # an active_since window.
            relay_state = RelayState(
                device=device,
                active=False,
                reported_total_active_seconds=report.total_active_seconds,
                reported_total_active_seconds_at_last_reset=report.total_active_seconds,
            )

        _apply_transition(relay_state, report, event_timestamp)

        relay_state.active = report.active
        relay_state.reported_total_active_seconds = report.total_active_seconds

        since_reset = relay_state.computed_total_active_seconds - relay_state.computed_total_active_seconds_at_last_reset
        relay_lifetime_alert_since_reset = since_reset if _update_relay_lifetime_alert_state(relay_state, since_reset) else None
        reported_since_reset = report.total_active_seconds - relay_state.reported_total_active_seconds_at_last_reset
        drift_alert = None if is_first_event else _update_drift_alert_state(device, relay_state, since_reset, reported_since_reset)

        logger.debug(
            f"Recording relay state report from {device}: "
            f"active={report.active}, "
            f"total_active_seconds={report.total_active_seconds}, "
            f"computed_total_active_seconds={relay_state.computed_total_active_seconds}, "
            f"since_reset={since_reset}, "
            f"timestamp={get_humanized_time(event_timestamp)} ({event_timestamp})"
        )

        await relay_state.save()

        await RelayStateHistory(
            device=device,
            timestamp=event_timestamp,
            active=report.active,
            reported_total_active_seconds=report.total_active_seconds,
            computed_total_active_seconds=relay_state.computed_total_active_seconds,
        ).save()

    return RelayReportOutcome(
        relay_lifetime_alert_since_reset=relay_lifetime_alert_since_reset,
        drift_alert=drift_alert,
    )


async def record_relay_state_reset(report: RelayResetReport, device: str) -> None:
    event_timestamp = get_timestamp(report.timestamp)

    async with _get_device_lock(device):
        relay_state = await get_relay_state_from_db(device) or RelayState(
            device=device,
            active=False,
            reported_total_active_seconds=0,
            reported_total_active_seconds_at_last_reset=0,
        )

        if relay_state.active and relay_state.active_since is not None:
            # The relay stayed on across the reset - fold the pre-reset portion of the current
            # session into the lifetime total (same as a real OFF transition would) and restart
            # the session at the reset point, so since_reset doesn't keep counting from whenever
            # the relay originally turned on.
            relay_state.computed_total_active_seconds += (event_timestamp - relay_state.active_since).total_seconds()
            relay_state.active_since = event_timestamp

        relay_state.computed_total_active_seconds_at_last_reset = relay_state.computed_total_active_seconds
        relay_state.lifetime_alert = AlertState()
        # The reset also zeroes S.M.I.B.H.I.D.'s own counter, so rebaseline the cross-check value
        # and drift bookkeeping - otherwise the next drift check compares the new since_reset=0
        # against the stale pre-reset reported total and falsely fires.
        relay_state.reported_total_active_seconds = 0
        relay_state.reported_total_active_seconds_at_last_reset = 0
        relay_state.drift_alert = AlertState()

        await relay_state.save()

        await RelayResetHistory(
            device=device,
            timestamp=event_timestamp,
            previous_total_active_seconds=report.previous_total_active_seconds,
            computed_total_active_seconds_at_reset=relay_state.computed_total_active_seconds,
        ).save()

    logger.info(
        f"Relay on-time counter reset for {device}: "
        f"previous_total_active_seconds={report.previous_total_active_seconds}, "
        f"computed_total_active_seconds_at_reset={relay_state.computed_total_active_seconds}, "
        f"timestamp={get_humanized_time(event_timestamp)} ({event_timestamp})"
    )


async def check_relay_state_for_alerts(relay_state: RelayState) -> RelayReportOutcome:
    """
    Periodic (non-event-triggered) re-check of a single device's relay state, used by the
    scheduled monitor job. Relay-lifetime uses a live-adjusted since_reset (accounting for an
    in-progress ON session that hasn't gone through an OFF transition yet, so a relay stuck ON
    still gets caught); drift stays on the stored since_reset, since the device's last reported
    total is also a stale snapshot and live-adjusting only one side would manufacture false drift.
    """
    now = datetime.now(UTC)

    async with _get_device_lock(relay_state.device):
        live_computed_total_active_seconds = relay_state.computed_total_active_seconds
        if relay_state.active_since is not None:
            live_computed_total_active_seconds += (now - relay_state.active_since).total_seconds()
        live_since_reset = live_computed_total_active_seconds - relay_state.computed_total_active_seconds_at_last_reset

        since_reset = relay_state.computed_total_active_seconds - relay_state.computed_total_active_seconds_at_last_reset
        reported_since_reset = relay_state.reported_total_active_seconds - relay_state.reported_total_active_seconds_at_last_reset

        relay_lifetime_alert_since_reset = live_since_reset if _update_relay_lifetime_alert_state(relay_state, live_since_reset) else None
        drift_alert = _update_drift_alert_state(relay_state.device, relay_state, since_reset, reported_since_reset)

        await relay_state.save()

    return RelayReportOutcome(
        relay_lifetime_alert_since_reset=relay_lifetime_alert_since_reset,
        drift_alert=drift_alert,
    )
