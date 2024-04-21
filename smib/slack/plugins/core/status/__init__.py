__plugin_name__ = "Status"
__description__ = "SMIB Status"
__author__ = "Sam Cork"

from pprint import pprint
from urllib.request import Request

from injectable import inject

from smib.common.utils import http_bolt_response
from smib.slack.custom_app import CustomApp

app: CustomApp = inject("SlackApp")



@app.middleware
def context_injector(context, next):
    plugin_manager = inject("PluginManager")
    scheduler = inject("Scheduler")
    context['plugin_manager'] = plugin_manager
    context['scheduler'] = scheduler

    next()


@app.event('http_get_status')
@http_bolt_response
def status(request: Request):
    plugin_manager = inject("PluginManager")
    scheduler = inject("Scheduler")
    data = {
        "plugin_count": len(plugin_manager.plugins),
        "plugins": [plugin.to_json_dict() for plugin in plugin_manager],
        "scheduled_jobs": [job.id for job in scheduler.get_jobs()]
    }
    return data

#
# @app.schedule('interval', '123', seconds=5, name='Testicle')
# def scheduled_task(say):
#     say("Scheduled Testing Testicle", channel="random")
#
#
# @app.schedule('interval', '123', seconds=10, name='Testicle2')
# def scheduled_task(say):
#     say("Scheduled Testing Testicle 2", channel="random")
