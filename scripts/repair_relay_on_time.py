#!/usr/bin/env python
"""
Rebuild a device's authoritative relay on-time by replaying its stored event history.

Why this exists
---------------
The relay plugin's first schema (commit 8dd3115) stored a field named `total_active_seconds`
in the `space_relay_state` collection. A later schema renamed that to
`reported_total_active_seconds` and introduced `computed_total_active_seconds` and
`active_since`, with no migration. When the new code loaded one of those legacy documents it
inherited `active=True` while `active_since` was absent and `computed_total_active_seconds`
defaulted to 0, so the next OFF transition measured a session against a meaningless
`active_since` and credited the result straight to the authoritative total. On SMIBHID-FAN
that single event banked 1744042s (~20.2 days) of on-time that never happened.

The same episode also left the two reset baselines disagreeing:
`computed_total_active_seconds_at_last_reset` restarted at 0 while
`reported_total_active_seconds_at_last_reset` kept a device lifetime counter, so
"since reset" meant one thing to the drift check and another to the lifetime alert.

`_apply_transition` now refuses implausible session durations and the bootstrap seeds both
baselines together, but neither fix is retroactive - the bad total is already persisted. This
script recomputes it from `space_relay_state_history`, which holds every event received and is
therefore a sound basis for a replay.

Note that the corruption is not itself visible as a rejectable event: the bogus `active_since`
was never written to history, so the replay simply never reproduces that credit. The
implausible-duration guard here is a safety net for other devices/records, not the mechanism
that fixes SMIBHID-FAN.

What it does
------------
Replays the device's history in timestamp order through the *current* transition rules, then
rewrites `computed_total_active_seconds`, `computed_total_active_seconds_at_last_reset`,
`active_since` and the reported-side baselines so both sides of "since reset" agree again.
Any reset recorded in `space_relay_state_reset_history` is applied at the point it occurred.

Defaults to a dry run: it prints the old and new values and exits without writing. Pass
--apply to persist, which also writes a timestamped backup of the pre-repair document.

Usage
-----
    # from the repo root, against a local/forwarded Mongo
    uv run python scripts/repair_relay_on_time.py --device SMIBHID-FAN
    uv run python scripts/repair_relay_on_time.py --device SMIBHID-FAN --apply

Point it at a remote Mongo with the standard settings, e.g.
`SMIB_DB_MONGO_DB_HOST=smib-pi`. Take a mongodump first if you want a full escape hatch;
--apply only backs up the single document it rewrites.
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

# Make `src/` importable when run directly from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from beanie import init_beanie  # noqa: E402
from pymongo import AsyncMongoClient  # noqa: E402

from plugins.space.relaystate.common import (  # noqa: E402
    _apply_transition,
    _reconcile_with_reported,
)
from plugins.space.relaystate.config import config  # noqa: E402
from plugins.space.relaystate.models import (  # noqa: E402
    AlertState,
    RelayResetHistory,
    RelayState,
    RelayStateHistory,
    RelayStateReport,
)
from smib.config import database  # noqa: E402

logger = logging.getLogger("repair_relay_on_time")


class ReplayResult:
    def __init__(self) -> None:
        self.computed_total_active_seconds = 0.0
        self.computed_total_active_seconds_at_last_reset = 0.0
        self.active_since: datetime | None = None
        self.active = False
        self.events_replayed = 0
        self.resets_applied = 0
        self.sessions_credited = 0
        self.sessions_rejected = 0
        self.rejected_seconds = 0.0
        self.reconciliations = 0
        self.reconciled_seconds = 0.0


def replay(events: list[RelayStateHistory], resets: list[RelayResetHistory]) -> ReplayResult:
    """
    Recompute cumulative on-time from the event stream.

    Drives the production helpers (_apply_transition, _reconcile_with_reported) against a
    scratch RelayState rather than reimplementing them, so the replay cannot answer
    differently from live processing. An earlier version did hand-roll the transition rules
    and immediately fell out of step when reconciliation was added to the plugin.

    The reported-side baseline is seeded the way the bootstrap seeds it - from the first
    observed reading - so reconciliation compares like with like from the very first event.
    """
    result = ReplayResult()
    if not events:
        return result

    ordered_events = sorted(events, key=lambda e: e.timestamp)
    pending_resets = sorted(resets, key=lambda r: r.timestamp)
    reset_index = 0

    # Scratch document the production helpers mutate. Seeded as record_relay_state_report's
    # bootstrap would seed it for this device's first event.
    state = RelayState.model_construct(
        device=ordered_events[0].device,
        active=False,
        active_since=None,
        computed_total_active_seconds=0.0,
        computed_total_active_seconds_at_last_reset=0.0,
        reported_total_active_seconds=ordered_events[0].reported_total_active_seconds,
        reported_total_active_seconds_at_last_reset=ordered_events[0].reported_total_active_seconds,
        lifetime_alert=AlertState(),
        drift_alert=AlertState(),
    )

    for index, event in enumerate(ordered_events):
        # Apply any reset that happened before this event, mirroring
        # record_relay_state_reset: fold the in-progress portion of an open session into the
        # total, restart the session at the reset point, then rebaseline both sides.
        while reset_index < len(pending_resets) and pending_resets[reset_index].timestamp <= event.timestamp:
            reset_at = pending_resets[reset_index].timestamp
            if state.active and state.active_since is not None:
                partial = (reset_at - state.active_since).total_seconds()
                if 0 <= partial <= config.max_plausible_on_session_seconds:
                    state.computed_total_active_seconds += partial
                state.active_since = reset_at
            state.computed_total_active_seconds_at_last_reset = state.computed_total_active_seconds
            state.reported_total_active_seconds = 0.0
            state.reported_total_active_seconds_at_last_reset = 0.0
            result.resets_applied += 1
            reset_index += 1

        report = RelayStateReport.model_construct(
            active=event.active,
            total_active_seconds=event.reported_total_active_seconds,
            timestamp=event.timestamp.timestamp(),
        )

        before = state.computed_total_active_seconds
        session_start = state.active_since

        _apply_transition(state, report, event.timestamp)
        state.active = event.active

        # Attribute the transition's outcome for the summary. A credited session advances the
        # total; a rejected one leaves it flat despite closing an open session.
        if session_start is not None and state.active_since is None and not event.active:
            if state.computed_total_active_seconds > before:
                result.sessions_credited += 1
            else:
                implied = (event.timestamp - session_start).total_seconds()
                result.sessions_rejected += 1
                result.rejected_seconds += max(implied, 0.0)

        # Reconcile exactly where record_relay_state_report does: after the transition, before
        # the reported baseline advances, and never on the first event (no history to correct).
        if index > 0:
            correction = _reconcile_with_reported(state, report)
            if correction is not None:
                result.reconciliations += 1
                result.reconciled_seconds += abs(correction)

        state.reported_total_active_seconds = event.reported_total_active_seconds
        result.events_replayed += 1

    # Any reset recorded after the final event.
    while reset_index < len(pending_resets):
        state.computed_total_active_seconds_at_last_reset = state.computed_total_active_seconds
        result.resets_applied += 1
        reset_index += 1

    result.computed_total_active_seconds = state.computed_total_active_seconds
    result.computed_total_active_seconds_at_last_reset = state.computed_total_active_seconds_at_last_reset
    result.active_since = state.active_since
    result.active = state.active
    return result


def resolve_reported_baseline(
    events: list[RelayStateHistory],
    resets: list[RelayResetHistory],
) -> float:
    """
    The reported-side value that corresponds to the replay's reset point, so both sides of
    "since reset" cover the same window.

    With no recorded reset the replay starts from 0 at the device's first observed event, but
    the device's own counter was already mid-life then - so the baseline is that first reading
    (what the bootstrap seeds), not 0. Using 0 would leave a residual drift equal to the
    device's entire pre-SMIB lifetime, which is the skew this script exists to remove.
    """
    if resets:
        return max(resets, key=lambda r: r.timestamp).previous_total_active_seconds
    return min(events, key=lambda e: e.timestamp).reported_total_active_seconds


def summarise(relay_state: RelayState, result: ReplayResult, reported_at_last_reset: float) -> str:
    def days(seconds: float) -> str:
        return f"{seconds:.0f}s ({seconds / 86400:.2f}d)"

    old_computed_since_reset = (
        relay_state.computed_total_active_seconds
        - relay_state.computed_total_active_seconds_at_last_reset
    )
    new_computed_since_reset = (
        result.computed_total_active_seconds
        - result.computed_total_active_seconds_at_last_reset
    )
    reported_since_reset = relay_state.reported_total_active_seconds - reported_at_last_reset

    # A relay that is still on leaves a legitimate gap: the device credits the in-flight
    # session continuously while the computed side only banks it at the next OFF. That is not
    # drift, and comparing it against the drift threshold would misreport a healthy repair.
    residual = abs(new_computed_since_reset - reported_since_reset)
    if result.active and result.active_since is not None:
        residual_note = " (the in-progress ON session, not yet banked - expected)"
    else:
        residual_note = f" (drift threshold {config.total_active_seconds_drift_warning_threshold_seconds:.0f}s)"

    lines = [
        f"Device:                  {relay_state.device}",
        f"Events replayed:         {result.events_replayed}",
        f"Resets applied:          {result.resets_applied}",
        f"Sessions credited:       {result.sessions_credited}",
        f"Sessions rejected:       {result.sessions_rejected} "
        f"({days(result.rejected_seconds)} not credited)",
        f"Reconciliations:         {result.reconciliations} "
        f"({days(result.reconciled_seconds)} of drift corrected against the device counter)",
        "",
        "computed_total_active_seconds:",
        f"  before:                {days(relay_state.computed_total_active_seconds)}",
        f"  after:                 {days(result.computed_total_active_seconds)}",
        "",
        "computed_total_active_seconds_at_last_reset:",
        f"  before:                {days(relay_state.computed_total_active_seconds_at_last_reset)}",
        f"  after:                 {days(result.computed_total_active_seconds_at_last_reset)}",
        "",
        "reported_total_active_seconds_at_last_reset:",
        f"  before:                {days(relay_state.reported_total_active_seconds_at_last_reset)}",
        f"  after:                 {days(reported_at_last_reset)}",
        "",
        "since-reset agreement (drives drift + lifetime alerts):",
        f"  before:                computed={days(old_computed_since_reset)} "
        f"reported={days(relay_state.reported_total_active_seconds - relay_state.reported_total_active_seconds_at_last_reset)}",
        f"  after:                 computed={days(new_computed_since_reset)} "
        f"reported={days(reported_since_reset)}",
        f"  residual after:        {residual:.0f}s{residual_note}",
        "",
        f"active:                  {relay_state.active} -> {result.active}",
        f"active_since:            {relay_state.active_since} -> {result.active_since}",
    ]
    return "\n".join(lines)


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild a device's relay on-time totals by replaying stored history.",
    )
    parser.add_argument("--device", required=True, help="Device hostname, e.g. SMIBHID-FAN")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist the repair. Without this the script only reports what it would change.",
    )
    parser.add_argument(
        "--backup-dir",
        default=".",
        help="Directory for the pre-repair document backup written by --apply (default: cwd)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    client = AsyncMongoClient(database.mongo_db_uri, tz_aware=True)
    await init_beanie(
        database=client[database.mongo_db_name],
        document_models=[RelayState, RelayStateHistory, RelayResetHistory],
    )

    relay_state = await RelayState.find_one(RelayState.device == args.device)
    if relay_state is None:
        logger.error(f"No relay state found for device {args.device}")
        return 1

    events = await RelayStateHistory.find(RelayStateHistory.device == args.device).to_list()
    resets = await RelayResetHistory.find(RelayResetHistory.device == args.device).to_list()

    if not events:
        logger.error(
            f"No history for {args.device} - nothing to replay. Refusing to rewrite the "
            f"total from an empty event stream."
        )
        return 1

    result = replay(events, resets)

    reported_at_last_reset = resolve_reported_baseline(events, resets)

    print()
    print(summarise(relay_state, result, reported_at_last_reset))
    print()

    if not args.apply:
        print("Dry run - nothing written. Re-run with --apply to persist.")
        return 0

    backup_path = (
        Path(args.backup_dir)
        / f"relay_state_backup_{args.device}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    backup_path.write_text(relay_state.model_dump_json(indent=2))
    logger.info(f"Wrote pre-repair backup to {backup_path}")

    relay_state.computed_total_active_seconds = result.computed_total_active_seconds
    relay_state.computed_total_active_seconds_at_last_reset = (
        result.computed_total_active_seconds_at_last_reset
    )
    relay_state.reported_total_active_seconds_at_last_reset = reported_at_last_reset
    relay_state.active_since = result.active_since
    relay_state.active = result.active

    await relay_state.save()
    logger.info(f"Repaired relay state for {args.device}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
