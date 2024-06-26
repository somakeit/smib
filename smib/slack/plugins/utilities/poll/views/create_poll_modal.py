from slack_sdk.models.blocks import InputBlock, Block
from slack_sdk.models.views import View

from smib.slack.utilities import Modal


class CreatePollModal(Modal):
    OPTION_PREFIX = 'poll_option'
    TITLE = 'Create Poll'
    SUBMIT_BUTTON_TEXT = 'Create'
    EXTERNAL_ID = 'create_poll_nodal'

    def __init__(self, /, **kwargs):
        kwargs['title'] = kwargs.get('title', self.TITLE)
        kwargs['submit'] = kwargs.get('submit', self.SUBMIT_BUTTON_TEXT)
        kwargs['external_id'] = kwargs.get('external_id', self.EXTERNAL_ID)

        super().__init__(**kwargs)

        self.blocks = [Block(**b) for b in kwargs.get('blocks', [])]

    def add_option_field(self):
        ...


