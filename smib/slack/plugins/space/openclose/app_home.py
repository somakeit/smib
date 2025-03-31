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
        f"So Make It is currently *{'open :large_green_circle:' if space.open else 'closed :red_circle:'}*!",
    )
    state_text_block = SectionBlock(text=state_text)
    space_state_blocks.append(state_text_block)

    space_open_button_highlight = space.open is None or not space.open
    space_closed_button_highlight = space.open is None or space.open

    # Buttons
    open_button = ButtonElement(
        text=PlainTextObject(text=f"{':large_green_circle: ' if space_open_button_highlight else ''}Set Space Open", emoji=True),
        value="open",
        action_id="space_open",
        style="primary" if space_open_button_highlight else None
    )

    closed_button = ButtonElement(
        text=PlainTextObject(text=f"{':red_circle: ' if space_closed_button_highlight else ''}Set Space Closed", emoji=True),
        value="closed",
        action_id="space_closed",
        style="danger" if space_closed_button_highlight else None
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
