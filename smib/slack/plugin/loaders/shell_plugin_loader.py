import subprocess
import shlex
from smib.slack.plugin.loaders.abstract_plugin_loader import AbstractPluginLoader
from pathlib import Path
from injectable import injectable, inject
import json
from smib.slack.plugin import PluginMeta, PluginType, Plugin
from slack_bolt import App
from slack_sdk.web.slack_response import SlackResponse


@injectable(qualifier="PluginLoader")
class ShellPluginLoader(AbstractPluginLoader):
    type: PluginType = PluginType.SHELL
    id_file: Path = Path('plugin.json')
    app: App = inject(App)

    def register_plugin(self, plugin: Plugin) -> Plugin:
        try:
            plugin_id_file = open(plugin.directory / self.id_file)
            plugin_id_file_json = json.load(plugin_id_file)
        except Exception as e:
            plugin.enabled = False
            plugin.error = f"{e.__class__.__name__}: {e}"
        else:
            plugin_meta = PluginMeta(
                name=plugin_id_file_json.get("name", plugin.id),
                description=plugin_id_file_json.get("description", None),
                author=plugin_id_file_json.get("author", None)
            )
            plugin.metadata = plugin_meta

            hooks = plugin_id_file_json.get("hooks", [])
            for hook in hooks:
                method = getattr(self.app, hook.get("event_type", None))
                if method is not None:
                    script = plugin.directory / hook.get("script", None)
                    if script.exists():
                        script_callable = ShellScript(script)
                        method(**hook.get("event_arguments", {}))(script_callable.run)

        return plugin

    def unregister_plugin(self, plugin: Plugin) -> None:
        # Do nothing for shell - already handled by the base unload_plugin method
        pass


class ShellScript:
    def __init__(self, script: Path) -> None:
        self.script = script

    def run(self, event, client, *args, **kwargs):
        parameters = [
            event.get("user", None),
            event.get("channel", None),
            event.get("type"),
            event.get("text", None)
        ]
        command = f"{self.script} {shlex.join(parameters)}"
        completed_process = subprocess.run(command, capture_output=True, text=True, shell=True)
        print(completed_process.stdout)
        if completed_process.stderr:
            print(f"Errors: {completed_process.stderr}")
