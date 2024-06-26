from enum import Enum
from slack_sdk.models.views import View


class ViewType(Enum):
    MODAL = 'modal'


class Modal(View):
    def __init__(self, /, **kwargs):
        kwargs['type'] = ViewType.MODAL.value
        super().__init__(**kwargs)
