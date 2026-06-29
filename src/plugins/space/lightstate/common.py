import logging

from .models import SpaceLightState, SpaceLightStateHistory, SpaceLightStateReport

logger = logging.getLogger("Space Light State Plugin - Common")


async def get_light_state_from_db(device: str) -> SpaceLightState | None:
    return await SpaceLightState.find_one(SpaceLightState.device == device)


async def log_to_space_light_state_history(report: SpaceLightStateReport, device: str) -> None:
    await SpaceLightStateHistory(
        device=device,
        light_state=report.light_state,
        light_value_lux=report.light_value_lux,
        threshold_lux=report.threshold_lux,
    ).save()


async def set_light_state_in_db(report: SpaceLightStateReport, device: str) -> SpaceLightState:
    logger.debug(f"Setting light state for {device} in DB")

    light_state = await get_light_state_from_db(device) or SpaceLightState(
        device=device,
        light_state=report.light_state,
        light_value_lux=report.light_value_lux,
        threshold_lux=report.threshold_lux,
    )

    light_state.light_state = report.light_state
    light_state.light_value_lux = report.light_value_lux
    light_state.threshold_lux = report.threshold_lux

    await light_state.save()
    return light_state

async def record_light_state_report(report: SpaceLightStateReport, device: str) -> None:
    logger.debug(
        f"Recording light state report from {device}: "
        f"light_state={report.light_state}, "
        f"light_value_lux={report.light_value_lux}, "
        f"threshold_lux={report.threshold_lux}"
    )

    await set_light_state_in_db(report, device)
    await log_to_space_light_state_history(report, device)
