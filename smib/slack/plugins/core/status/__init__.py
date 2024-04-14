__plugin_name__ = "Status"
__description__ = "SMIB Status"
__author__ = "Sam Cork"

from pprint import pprint
from urllib.request import Request

from injectable import inject
from slack_bolt import App

from smib.common.utils import http_bolt_response
from smib.slack.custom_app import CustomApp

app: CustomApp = inject(App)
plugin_manager = inject("PluginManager")


@app.event('http_get_status')
@http_bolt_response
def status(request: Request):
    data = {
        "plugin_count": len(plugin_manager.plugins),
        "plugins": [plugin.to_json_dict() for plugin in plugin_manager],
        "test": False
    }
    return data


@app.schedule('interval', '123', seconds=5)
def scheduled_task(say):
    print('scheduled')
    say("Scheduled Testing Testicle", channel="random")

@app.schedule('interval', '123', seconds=10)
def scheduled_task(say):
    print('scheduled')
    say("Scheduled Testing Testicle 2", channel="random")
