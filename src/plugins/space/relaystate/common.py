import logging
from datetime import datetime, UTC, timedelta
from typing import NamedTuple

from smib.utilities import get_humanized_time, get_humanized_timedelta
from .config import config
from .models import RelayState, RelayStateHistory, RelayStateReport, RelayResetReport, RelayResetHistory
from ..smibhid.common import get_timestamp

logger = logging.getLogger("Space Relay State Plugin - Common")


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
        relay_state.computed_total_active_seconds += duration
        relay_state.active_since = None
    elif not is_on and relay_state.active_since is not None:
        # Turning off with a stale/unexpected active_since (e.g. missed the matching ON) - just clear it.
        relay_state.active_since = None


def _check_relay_lifetime(relay_state: RelayState, since_reset: float) -> bool:
    if config.relay_lifetime_warning_threshold is None:
        return False
    if since_reset < config.relay_lifetime_warning_threshold.total_seconds():
        return False

    now = datetime.now(UTC)
    first_alert = not relay_state.relay_lifetime_alert_sent
    resend_alert = (
        relay_state.relay_lifetime_alert_sent
        and config.relay_lifetime_alert_resend_interval is not None
        and relay_state.relay_lifetime_alert_last_sent_at is not None
        and (now - relay_state.relay_lifetime_alert_last_sent_at) > config.relay_lifetime_alert_resend_interval
    )
    should_alert = first_alert or resend_alert

    if not should_alert:
        return False

    relay_state.relay_lifetime_alert_sent = True
    relay_state.relay_lifetime_alert_last_sent_at = now
    return True


def _evaluate_drift(device: str, relay_state: RelayState, since_reset: float, reported_total_active_seconds: float) -> DriftAlertInfo | None:
    delta = abs(since_reset - reported_total_active_seconds)
    over_threshold = delta > config.total_active_seconds_drift_warning_threshold_seconds

    if over_threshold:
        logger.warning(
            f"Relay state total_active_seconds drift for {device} exceeds threshold "
            f"({config.total_active_seconds_drift_warning_threshold_seconds}s): "
            f"computed_since_reset={since_reset}s, "
            f"reported={reported_total_active_seconds}s, delta={delta}s"
        )

    now = datetime.now(UTC)
    first_alert = over_threshold and not relay_state.drift_alert_active
    resend_alert = (
        over_threshold
        and relay_state.drift_alert_active
        and config.drift_warning_alert_resend_interval is not None
        and relay_state.drift_alert_last_sent_at is not None
        and (now - relay_state.drift_alert_last_sent_at) > config.drift_warning_alert_resend_interval
    )
    should_alert = first_alert or resend_alert

    relay_state.drift_alert_active = over_threshold

    if not should_alert:
        return None

    relay_state.drift_alert_last_sent_at = now
    return DriftAlertInfo(since_reset=since_reset, reported=reported_total_active_seconds, delta=delta)


def build_relay_lifetime_alert_message(since_reset: float, device: str) -> str:
    return config.relay_lifetime_alert_message_template.format(
        relay_name=config.relay_name,
        device=device,
        duration=get_humanized_timedelta(timedelta(seconds=since_reset)),
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
        )

    _apply_transition(relay_state, report, event_timestamp)

    relay_state.active = report.active
    relay_state.reported_total_active_seconds = report.total_active_seconds

    since_reset = relay_state.computed_total_active_seconds - relay_state.computed_total_active_seconds_at_last_reset
    relay_lifetime_alert_since_reset = since_reset if _check_relay_lifetime(relay_state, since_reset) else None
    drift_alert = None if is_first_event else _evaluate_drift(device, relay_state, since_reset, report.total_active_seconds)

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
    relay_state = await get_relay_state_from_db(device) or RelayState(
        device=device,
        active=False,
        reported_total_active_seconds=report.previous_total_active_seconds,
    )

    event_timestamp = get_timestamp(report.timestamp)

    relay_state.computed_total_active_seconds_at_last_reset = relay_state.computed_total_active_seconds
    relay_state.last_reset_at = event_timestamp
    relay_state.last_reset_previous_total_active_seconds = report.previous_total_active_seconds
    relay_state.relay_lifetime_alert_sent = False
    relay_state.relay_lifetime_alert_last_sent_at = None

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

    live_computed_total_active_seconds = relay_state.computed_total_active_seconds
    if relay_state.active_since is not None:
        live_computed_total_active_seconds += (now - relay_state.active_since).total_seconds()
    live_since_reset = live_computed_total_active_seconds - relay_state.computed_total_active_seconds_at_last_reset

    since_reset = relay_state.computed_total_active_seconds - relay_state.computed_total_active_seconds_at_last_reset

    relay_lifetime_alert_since_reset = live_since_reset if _check_relay_lifetime(relay_state, live_since_reset) else None
    drift_alert = _evaluate_drift(relay_state.device, relay_state, since_reset, relay_state.reported_total_active_seconds)

    await relay_state.save()

    return RelayReportOutcome(
        relay_lifetime_alert_since_reset=relay_lifetime_alert_since_reset,
        drift_alert=drift_alert,
    )
