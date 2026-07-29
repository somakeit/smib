import logging

from datetime import UTC

from .models import (
    RelayResetHistory,
    RelayState,
    RelayStateHistory,
    RelayStateResetRequest,
    RelayStateUpdateRequest,
)

logger = logging.getLogger("Relay State Plugin - Common")


async def get_relay_state_from_db(device: str) -> RelayState | None:
    return await RelayState.find_one(RelayState.device == device)


def to_utc(timestamp):
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)

    return timestamp.astimezone(UTC)


async def log_to_relay_state_history(report: RelayStateUpdateRequest, device: str) -> None:
    await RelayStateHistory(
        device=device,
        active=report.active,
        smibhid_timestamp=to_utc(report.timestamp),
        total_active_seconds=report.total_active_seconds,
    ).save()


async def log_to_relay_reset_history(report: RelayStateResetRequest, device: str) -> None:
    await RelayResetHistory(
        device=device,
        smibhid_timestamp=to_utc(report.timestamp),
        previous_total_active_seconds=report.previous_total_active_seconds,
    ).save()


async def set_relay_state_in_db(report: RelayStateUpdateRequest, device: str) -> RelayState:
    logger.debug(f"Setting relay state for {device} in DB")

    relay_state = await get_relay_state_from_db(device) or RelayState(
        device=device,
        active=report.active,
        smibhid_timestamp=report.timestamp,
        total_active_seconds=report.total_active_seconds,
    )

    relay_state.active = report.active
    relay_state.smibhid_timestamp = to_utc(report.timestamp)
    relay_state.total_active_seconds = report.total_active_seconds

    await relay_state.save()
    return relay_state


async def record_relay_state_update(report: RelayStateUpdateRequest, device: str) -> None:
    logger.debug(
        f"Recording relay state update from {device}: "
        f"active={report.active}, "
        f"timestamp={report.timestamp}, "
        f"total_active_seconds={report.total_active_seconds}"
    )

    await set_relay_state_in_db(report, device)
    await log_to_relay_state_history(report, device)


async def record_relay_reset(report: RelayStateResetRequest, device: str) -> None:
    logger.debug(
        f"Recording relay reset from {device}: "
        f"timestamp={report.timestamp}, "
        f"previous_total_active_seconds={report.previous_total_active_seconds}"
    )

    await log_to_relay_reset_history(report, device)