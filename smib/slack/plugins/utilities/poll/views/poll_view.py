from slack_sdk.models.blocks import InputBlock, Block
from slack_sdk.models.views import View


class PollView(View):
    OPTION_PREFIX = 'poll_option'

    @property
    def options(self) -> list[InputBlock]:
        return list(filter(lambda block: block.block_id is not None and block.block_id.startswith(self.OPTION_PREFIX),
                           self.blocks))
