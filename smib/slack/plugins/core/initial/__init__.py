__plugin_name__ = "Core Initialisation"
__description__ = ""
__author__ = "Sam Cork"

import re

from injectable import inject
from smib.slack.custom_app import CustomApp

app: CustomApp = inject("SlackApp")


@app.hello()
def hello_world(request, context):
    context['logger'].debug('Hello World!')
    context['logger'].debug(f"{request.body['num_connections']=}")
