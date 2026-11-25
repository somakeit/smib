from datetime import UTC, datetime, timedelta

from slack_sdk.models.blocks import Block, MarkdownTextObject, SectionBlock

from smib.utilities import get_humanized_time
from .models import SpaceLightState

# The same per-device settings /howfresh uses: a device named "Clean Room" in one readout
# should not appear as a bare hostname in the other.
from ..smibhid.config import config as device_config

STALE_MARKER = ":warning:"


def as_utc(timestamp: datetime) -> datetime:
    # MongoDB stores dates without a zone, so a round-tripped document comes back naive even
    # though it was written as UTC.
    return timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp


def reading_age(light_state: SpaceLightState, observed_at: datetime | None = None) -> timedelta:
    """
    How long ago the light level behind this state was actually measured.

    `updated_at` is when SMIB last wrote the document, refreshed on every save, and the light
    state report carries no device-side timestamp at all - so a device that reconnects after a
    week offline and pushes once looks instantly fresh. `observed_at` is the device's own
    sensor log timestamp, which is the honest clock; it is only a fallback to `updated_at`
    when a device has reported light state but no sensor log.
    """
    return datetime.now(UTC) - as_utc(observed_at or light_state.updated_at)


def is_stale(light_state: SpaceLightState, observed_at: datetime | None = None) -> bool:
    return reading_age(light_state, observed_at) > device_config.stale_after_for(light_state.device)


def is_excluded(light_state: SpaceLightState, observed_at: datetime | None = None) -> bool:
    exclude_after = device_config.exclude_after_for(light_state.device)
    return exclude_after is not None and reading_age(light_state, observed_at) > exclude_after


def select_states_to_render(
        light_states: list[SpaceLightState],
        observed_at: dict[str, datetime] | None = None,
) -> list[SpaceLightState]:
    """
    Drop devices whose light state is too old to describe the space now, then order them.

    As in /howfresh, a device is only ever dropped while another is still reporting - if
    every device is that stale they are all kept and marked, since a stale answer beats
    claiming the light state is unknown when a reading exists.
    """
    observed_at = observed_at or {}
    included = [
        state for state in light_states if not is_excluded(state, observed_at.get(state.device))
    ] or light_states

    return sorted(included, key=lambda state: device_config.sort_key_for(state.device))


def describe_light_state(light_state: SpaceLightState) -> str:
    return (
        ":bulb: Lights appear to be *on*"
        if light_state.light_state
        else ":new_moon: Lights appear to be *off*"
    )


def build_device_line(light_state: SpaceLightState, observed_at: datetime | None) -> str:
    label = device_config.display_name(light_state.device)
    marker = f" {STALE_MARKER}" if is_stale(light_state, observed_at) else ""
    measured_at = observed_at or light_state.updated_at

    return (
        f"{describe_light_state(light_state)} in *{label}*{marker}\n"
        f"_{light_state.light_value_lux:.2f} lx, threshold {light_state.threshold_lux:.2f} lx "
        f"· {get_humanized_time(measured_at)}_"
    )


async def get_observed_at_per_device() -> dict[str, datetime]:
    """
    When each device last actually measured anything, from its sensor log.

    The light state document only knows when SMIB wrote it, so on its own it cannot tell a
    live device from one that reconnected after a week and pushed a single report. The sensor
    log carries the device's own timestamp, which can.
    """
    try:
        from ..smibhid.sensor.models import SensorLog
    except ImportError:  # pragma: no cover - the sensor plugin should always be present
        return {}

    logs = await SensorLog.get_latest_log_per_device()
    return {log.device: as_utc(log.timestamp) for log in logs}


async def get_space_light_state_blocks() -> list[Block]:
    light_states = await SpaceLightState.get_states_per_device()

    if not light_states:
        return [
            SectionBlock(
                text=MarkdownTextObject(
                    text=":grey_question: Light state is currently unknown."
                )
            )
        ]

    observed_at = await get_observed_at_per_device()
    states = select_states_to_render(light_states, observed_at)

    # One device reads better as a single statement about the space than as a list of one.
    if len(states) == 1:
        light_state = states[0]
        device_observed_at = observed_at.get(light_state.device)
        marker = f" {STALE_MARKER}" if is_stale(light_state, device_observed_at) else ""
        measured_at = device_observed_at or light_state.updated_at

        return [
            SectionBlock(
                text=MarkdownTextObject(
                    text=(
                        f"{describe_light_state(light_state)}{marker}\n"
                        f"_Last updated {get_humanized_time(measured_at)} by "
                        f"{device_config.display_name(light_state.device)}_\n"
                        f"_({light_state.light_value_lux:.2f} lx, threshold "
                        f"{light_state.threshold_lux:.2f} lx)_"
                    )
                )
            )
        ]

    # Every device agreeing is the common case, and three identical lines is noise - so lead
    # with the shared answer and list the per-device levels underneath it.
    if len({state.light_state for state in states}) == 1:
        shared = describe_light_state(states[0])
        details = " · ".join(
            f"{device_config.display_name(state.device)} "
            f"{state.light_value_lux:.0f} lx"
            f"{STALE_MARKER if is_stale(state, observed_at.get(state.device)) else ''}"
            for state in states
        )

        return [SectionBlock(text=MarkdownTextObject(text=f"{shared} across the space\n_{details}_"))]

    return [
        SectionBlock(
            text=MarkdownTextObject(
                text="\n\n".join(
                    build_device_line(state, observed_at.get(state.device)) for state in states
                )
            )
        )
    ]
