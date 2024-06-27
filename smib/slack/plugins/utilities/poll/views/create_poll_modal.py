import json
from pathlib import Path
from pprint import pprint

from slack_sdk.models.blocks import InputBlock, Block, ActionsBlock, ButtonElement, DividerBlock, \
    ConversationSelectElement, PlainTextInputElement
from slack_sdk.models.views import View

from smib.slack.utilities import Modal


class CreatePollModal(Modal):
    OPTION_PREFIX = 'poll_option'
    TITLE = 'Create Poll'
    SUBMIT_BUTTON_TEXT = 'Create'
    EXTERNAL_ID = 'create_poll_modal'
    MAX_OPTIONS = 20
    MIN_OPTIONS = 2

    def __init__(self, /, **kwargs):
        kwargs['title'] = kwargs.get('title', self.TITLE)
        kwargs['submit'] = kwargs.get('submit', self.SUBMIT_BUTTON_TEXT)
        kwargs['external_id'] = kwargs.get('external_id', self.EXTERNAL_ID)

        kwargs['blocks'] = kwargs.get('blocks', self._fresh_blocks())

        super().__init__(**kwargs)

    def _fresh_blocks(self) -> list[dict | Block]:
        blocks = [
            InputBlock(label="Title", block_id="poll_title", element=PlainTextInputElement(action_id='poll_title')),
            *[
                InputBlock(block_id=f"{self.OPTION_PREFIX}_{i+1}", label=f"Option {i+1}", element=PlainTextInputElement(action_id=f"{self.OPTION_PREFIX}_{i+1}"))
                for i in range(self.MIN_OPTIONS)
            ],
            ActionsBlock(block_id="options_actions", elements=[
                ButtonElement(text="Add another option", action_id="add_option", style="primary"),
                ButtonElement(text="Remove option", action_id="remove_option", style="danger"),
            ]),
            DividerBlock(),
            InputBlock(block_id="channel_select", label="Select a channel",
                       element=ConversationSelectElement(placeholder="Select a channel", action_id='channel_select')),
        ]

        return blocks

    def add_option(self):
        current_blocks = self.blocks
        # Count current option blocks
        option_blocks = [block for block in current_blocks if
                         block.block_id and block.block_id.startswith(self.OPTION_PREFIX)]
        new_option_id = len(option_blocks) + 1
        if new_option_id > self.MAX_OPTIONS:
            return

        new_option_block = InputBlock(
            block_id=f"{self.OPTION_PREFIX}_{new_option_id}",
            label=f"Option {new_option_id}",
            element=PlainTextInputElement(action_id=f"{self.OPTION_PREFIX}_{new_option_id}")
        )
        # Insert the new option block before the ActionsBlock
        index = next(i for i, block in enumerate(current_blocks) if block.block_id == "options_actions")
        current_blocks.insert(index, new_option_block)
        self.blocks = current_blocks

    def remove_option(self):
        current_blocks = self.blocks
        # Find the last option block to remove
        option_blocks = [block for block in current_blocks if
                         block.block_id and block.block_id.startswith(self.OPTION_PREFIX)]
        if len(option_blocks) > self.MIN_OPTIONS:
            current_blocks.remove(option_blocks[-1])
        self.blocks = current_blocks


if __name__ == '__main__':
    view = CreatePollModal()
    pprint(view.__dict__, sort_dicts=False)

    path = Path(__file__).parent.parent / 'templates/new-poll.json'

    loaded_view = CreatePollModal.from_file(path)

    pprint(loaded_view.__dict__, sort_dicts=False)
