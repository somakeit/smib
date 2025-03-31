__plugin_name__ = "How Fresh?"
__description__ = "How fresh is the space?"
__author__ = "Sam Cork"

from injectable import inject

from smib.slack.custom_app import CustomApp

app: CustomApp = inject("SlackApp")

@app.command("/howfresh")
def how_fresh(ack):
    print(how_fresh)
    ack()