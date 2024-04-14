__plugin_name__ = "Plugin Management"
__description__ = "Plugin for manging plugins"
__author__ = "Sam Cork"

from injectable import inject
from slack_bolt import App

from smib.common.utils import http_bolt_response

app: App = inject(App)
plugin_manager = inject("PluginManager")


@app.event('http_get_reload_plugins')
@http_bolt_response
def reload(message, say):
    plugin_manager.reload_all_plugins()

    return 200
