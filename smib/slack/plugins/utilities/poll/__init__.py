__plugin_name__ = "SMIB Poll"
__description__ = "Create and track polls"
__author__ = "Sam Cork"

from injectable import inject

from smib.slack.custom_app import CustomApp
from slack_sdk.web.client import WebClient

app: CustomApp = inject("SlackApp")


@app.global_shortcut('smib-poll')
def smib_poll_shortcut(body, payload, ack, client: WebClient):
    ack()
    resp = client.chat_postEphemeral(channel='bot', user=body['user']['id'], text='Poll')



