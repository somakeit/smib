import asyncio
from unittest import case

from slack_sdk.models.blocks import PlainTextObject, HeaderBlock, MarkdownTextObject, SectionBlock, ButtonElement, \
    ActionsBlock, DividerBlock, Block, BlockElement, StaticSelectElement, Option
from slack_sdk.models.views import View

from .common import get_space_state_from_db
from .models import SpaceState


async def get_app_home() -> View:
    blocks = []

    blocks += [_get_header_block()]
    blocks += await _get_space_state_blocks()
    blocks += [_get_divider()]
    blocks += _get_info_blocks()

    result = View(type="home", blocks=blocks)

    return result


def _get_header_block() -> Block:
    header_text = PlainTextObject(text="Welcome to S.M.I.B.", emoji=True)
    header_block = HeaderBlock(text=header_text)
    return header_block

def _get_space_open_actions_block_elements() -> ActionsBlock:
    open_button = ButtonElement(
        text=PlainTextObject(text="Set Space Open", emoji=True),
        value="open",
        action_id="space_open_button",
        style="primary"
    )
    hours_static_select = StaticSelectElement(
        action_id="space_open_hours_select",
        placeholder=PlainTextObject(text="Select hours (optional)", emoji=True),
        options=[Option(value=f"{i}", text=f"{i}h") for i in range(10)],
    )
    action_block = ActionsBlock(block_id="space_open_block", elements=[open_button, hours_static_select])
    return action_block

def _get_space_close_actions_block_elements() -> ActionsBlock:
    closed_button = ButtonElement(
        text=PlainTextObject(text="Set Space Closed", emoji=True),
        value="closed",
        action_id="space_closed_button",
        style="danger"
    )
    action_block = ActionsBlock(block_id="space_closed_block", elements=[closed_button])
    return action_block


async def _get_space_state_blocks() -> list[Block]:
    space_state_blocks = []

    space: SpaceState = await get_space_state_from_db()

    state_text = MarkdownTextObject(text="")
    state_set_blocks: list[Block] = []

    match space.open:
        case True:
            state_text.text = ":large_green_circle: So Make It is currently *open!* :large_green_circle:"
            state_set_blocks.append(_get_space_close_actions_block_elements())
        case False:
            state_text.text = ":red_circle: So Make It is currently *closed!* :red_circle:"
            state_set_blocks.append(_get_space_open_actions_block_elements())
        case _:
            state_text.text = ":warning: Unable to determine if So Make It is open or closed! :warning:"
            state_set_blocks.append(_get_space_open_actions_block_elements())
            state_set_blocks.append(SectionBlock(text="OR"))
            state_set_blocks.append(_get_space_close_actions_block_elements())

    state_text_block = SectionBlock(text=state_text)
    space_state_blocks.append(state_text_block)
    space_state_blocks += state_set_blocks

    return space_state_blocks


def _get_divider() -> DividerBlock:
    divider = DividerBlock()
    return divider


def _get_info_blocks() -> list[Block]:
    info_blocks = []

    header = HeaderBlock(text="Useful Links")
    info_blocks.append(header)

    smib_header = SectionBlock(
        text=MarkdownTextObject(text="*For more information on S.M.I.B., visit the following links:*"),
    )
    info_blocks.append(smib_header)

    smib_actions = ActionsBlock(
        elements=[
            ButtonElement(
                text="GitHub Repo",
                url="https://github.com/somakeit/smib",
                action_id="app_home_url_smib_github_repo"
            ),
            ButtonElement(
                text="Issue Tracker",
                url="https://github.com/somakeit/smib/issues",
                action_id="app_home_url_smib_issue_tracker"
            ),
            ButtonElement(
                text="Contributing",
                url="https://github.com/somakeit/smib/contribute",
                action_id="app_home_url_smib_contributing"
            )
        ]
    )
    info_blocks.append(smib_actions)

    smibhid_header = SectionBlock(
        text=MarkdownTextObject(text="*For more information on S.M.I.B.H.I.D., visit the following links:*"),
    )
    info_blocks.append(smibhid_header)

    smibhid_actions = ActionsBlock(
        elements=[
            ButtonElement(
                text="GitHub Repo",
                url="https://github.com/somakeit/smibhid",
                action_id="app_home_url_smibhid_github_repo"
            ),
            ButtonElement(
                text="Issue Tracker",
                url="https://github.com/somakeit/smibhid/issues",
                action_id="app_home_url_smibhid_issue_tracker"
            ),
            ButtonElement(
                text="Contributing",
                url="https://github.com/somakeit/smibhid/contribute",
                action_id="app_home_url_smibhid_contributing"
            )
        ]
    )

    info_blocks.append(smibhid_actions)

    return info_blocks

def extract_selected_hours_from_state(state: dict) -> int:
    try:
        return int(state["values"]["space_open_block"]["space_open_hours_select"]["selected_option"]["value"])
    except (KeyError, TypeError, ValueError):
        return 0