__plugin_name__ = "Core Test"
__description__ = "Simple test plugin"
__author__ = "Sam Cork"

from injectable import inject
from slack_bolt import App

app: App = inject(App)

