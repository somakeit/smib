__plugin_name__ = "Core Test"
__description__ = "Simple test plugin"
__author__ = "Sam Cork"

from injectable import inject
from slack_bolt import App

app: App = inject(App)
plugin_manager = inject("PluginManager")


@app.message('reload')
def reload(message, say):
    say(text='testing testicle', channel=message['channel'])
    plugin_manager.reload_all_plugins()


@app.event('http_get_reload')
def reload(message, say):
    print('reload')
    plugin_manager.reload_all_plugins()
    for plugin in plugin_manager.plugins:
        print(plugin)