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

from plugins.space.relaystate.config import config  # noqa: E402
from plugins.space.relaystate.models import (  # noqa: E402
    RelayResetHistory,
    RelayState,
    RelayStateHistory,
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


def replay(events: list[RelayStateHistory], resets: list[RelayResetHistory]) -> ReplayResult:
    """
    Recompute cumulative on-time from the event stream.

    Mirrors the production rules in plugins.space.relaystate.common._apply_transition:
    time is only credited on an ON->OFF transition, out-of-order timestamps contribute 0,
    and a session longer than max_plausible_on_session_seconds is rejected rather than
    banked (this is what quarantines the original corruption instead of replaying it).
    """
    result = ReplayResult()
    pending_resets = sorted(resets, key=lambda r: r.timestamp)
    reset_index = 0

    for event in sorted(events, key=lambda e: e.timestamp):
        # Apply any reset that happened before this event. A reset folds the in-progress
        # portion of an open session into the total and rebaselines, matching
        # record_relay_state_reset.
        while reset_index < len(pending_resets) and pending_resets[reset_index].timestamp <= event.timestamp:
            reset_at = pending_resets[reset_index].timestamp
            if result.active and result.active_since is not None:
                partial = (reset_at - result.active_since).total_seconds()
                if 0 <= partial <= config.max_plausible_on_session_seconds:
                    result.computed_total_active_seconds += partial
                result.active_since = reset_at
            result.computed_total_active_seconds_at_last_reset = result.computed_total_active_seconds
            result.resets_applied += 1
            reset_index += 1

        was_on = result.active
        is_on = event.active

        if is_on and not was_on:
            result.active_since = event.timestamp
        elif not is_on and was_on and result.active_since is not None:
            duration = (event.timestamp - result.active_since).total_seconds()
            if duration < 0:
                logger.warning(
                    f"Out-of-order event at {event.timestamp.isoformat()} "
                    f"(active_since={result.active_since.isoformat()}); crediting 0s."
                )
                duration = 0.0
            elif duration > config.max_plausible_on_session_seconds:
                logger.warning(
                    f"Rejecting implausible session of {duration:.0f}s ending "
                    f"{event.timestamp.isoformat()} (active_since="
                    f"{result.active_since.isoformat()}) - this is the corruption being repaired."
                )
                result.sessions_rejected += 1
                result.rejected_seconds += duration
                duration = 0.0
            else:
                result.sessions_credited += 1
            result.computed_total_active_seconds += duration
            result.active_since = None
        elif not is_on and result.active_since is not None:
            result.active_since = None

        result.active = is_on
        result.events_replayed += 1

    # Any reset recorded after the final event.
    while reset_index < len(pending_resets):
        result.computed_total_active_seconds_at_last_reset = result.computed_total_active_seconds
        result.resets_applied += 1
        reset_index += 1

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

    lines = [
        f"Device:                  {relay_state.device}",
        f"Events replayed:         {result.events_replayed}",
        f"Resets applied:          {result.resets_applied}",
        f"Sessions credited:       {result.sessions_credited}",
        f"Sessions rejected:       {result.sessions_rejected} "
        f"({days(result.rejected_seconds)} not credited)",
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
        f"  residual drift after:  {abs(new_computed_since_reset - reported_since_reset):.0f}s "
        f"(threshold {config.total_active_seconds_drift_warning_threshold_seconds:.0f}s)",
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
