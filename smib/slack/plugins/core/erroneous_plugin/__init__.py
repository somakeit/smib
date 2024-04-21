
from injectable import inject

from smib.common.utils import http_bolt_response
from smib.slack.custom_app import CustomApp

app: CustomApp = inject("SlackApp")


@app.event('http_get_statis')
def http_get_statis(say, context):
    context['logger'].info(f"Slack")
    return 1/0
