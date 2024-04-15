__plugin_name__ = "Plugin Management"
__description__ = "Plugin for manging plugins"
__author__ = "Sam Cork"

import datetime
from pprint import pprint

from injectable import inject
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from smib.slack.custom_app import CustomApp as App

from smib.common.utils import http_bolt_response

app: App = inject("SlackApp")
plugin_manager = inject("PluginManager")
scheduler: BackgroundScheduler = inject("Scheduler")

@app.middleware
def context_injector_test(context, next):
    context['plugin_manager'] = plugin_manager
    context['scheduler'] = scheduler

    next()


@app.message('reload')
@app.event('http_get_reload_plugins')
@http_bolt_response
def reload(message, say, event):
    print('reloading plugins')
    plugin_manager.reload_all_plugins()

    return 200


# @app.schedule('interval', seconds=5, id='Test', name='Test')
# def test(context):
#     print(context)


@app.schedule('interval', seconds=60*15, id='reload_plugins_trigger', name='Trigger Schedule for Reloading Plugins')
def reload_plugins():
    next_run = datetime.datetime.now() + datetime.timedelta(seconds=1)
    app.schedule('date', id="reload_plugins", run_date=next_run, name="Scheduled Reload Plugins")(reload)


@app.schedule(CronTrigger.from_crontab('19 22 * * *'), id="quiet_time", name="Quiet Time")
def quiet_time(say):
    say('quiet time', channel='random')
