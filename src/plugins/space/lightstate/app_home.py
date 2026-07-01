from slack_sdk.models.blocks import Block, MarkdownTextObject, SectionBlock

from smib.utilities import get_humanized_time
from .models import SpaceLightState


async def get_space_light_state_blocks() -> list[Block]:
    light_state = await SpaceLightState.get_latest_state()

    if light_state is None:
        return [
            SectionBlock(
                text=MarkdownTextObject(
                    text=":grey_question: Light state is currently unknown."
                )
            )
        ]

    state_text = (
        ":bulb: Lights appear to be *on*"
        if light_state.light_state
        else ":new_moon: Lights appear to be *off*"
    )

    return [
        SectionBlock(
            text=MarkdownTextObject(
                text=(
                    f"{state_text}\n"
                    f"_Last updated {get_humanized_time(light_state.updated_at)} by {light_state.device}_\n"
                    f"_({light_state.light_value_lux:.2f} lx, threshold {light_state.threshold_lux:.2f} lx)_"
                )
            )
        )
    ]