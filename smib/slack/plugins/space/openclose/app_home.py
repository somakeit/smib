from slack_sdk.models.blocks import PlainTextObject, HeaderBlock, MarkdownTextObject, SectionBlock, ButtonElement, \
    ActionsBlock, DividerBlock, Block, BlockElement
from slack_sdk.models.views import View

from smib.slack.db import database
from .models import Space


def get_app_home() -> View:
    blocks = []

    blocks += [_get_header_block()]
    blocks += _get_space_state_blocks()
    blocks += [_get_divider()]
    blocks += _get_info_blocks()

    result = View(type="home", blocks=blocks)

    return result


def _get_header_block() -> Block:
    header_text = PlainTextObject(text="Welcome to S.M.I.B.", emoji=True)
    header_block = HeaderBlock(text=header_text)
    return header_block


@database()
def _get_space_state_blocks() -> list[Block]:
    space_state_blocks = []

    space = Space.single()

    # State Text
    state_text = MarkdownTextObject(
        text=":warning: Unable to determine if So Make It is open or closed! :warning:" if space.open is None else
        f"So Make It is currently *{'open' if space.open else 'closed'}*!",
    )
    state_text_block = SectionBlock(text=state_text)
    space_state_blocks.append(state_text_block)

    # Buttons
    open_button = ButtonElement(
        text=PlainTextObject(text=":large_green_circle: Space Open", emoji=True),
        value="open",
        action_id="space_open",
        style="primary" if space.open is None or not space.open else None
    )

    closed_button = ButtonElement(
        text=PlainTextObject(text=":red_circle: Space Closed", emoji=True),
        value="closed",
        action_id="space_closed",
        style="danger" if space.open is None or space.open else None
    )

    # Action block with buttons
    action_block = ActionsBlock(elements=[open_button, closed_button])
    space_state_blocks.append(action_block)

    return space_state_blocks


def _get_divider() -> DividerBlock:
    divider = DividerBlock()
    return divider


def _get_info_blocks() -> list[Block]:
    info_blocks = []

    section = SectionBlock(
        text="For more information see the GitHub repository",
        accessory=ButtonElement(
            text="GitHub Repo",
            url="https://github.com/somakeit/S.M.I.B.",
            action_id="app_home_url_github_repo"
        )
    )
    info_blocks.append(section)

    section = SectionBlock(
        text="To raise a bug or enhancement idea, visit our issue tracker",
        accessory=ButtonElement(
            text="Issue Tracker",
            url="https://github.com/somakeit/S.M.I.B./issues",
            action_id="app_home_url_issue_tracker"
        )
    )
    info_blocks.append(section)

    section = SectionBlock(
        text="How to contribute patches to code or documentation?",
        accessory=ButtonElement(
            text="Contributing",
            url="https://github.com/somakeit/S.M.I.B./blob/master/CONTRIBUTING.md",
            action_id="app_home_url_contributing"
        )
    )
    info_blocks.append(section)

    return info_blocks
