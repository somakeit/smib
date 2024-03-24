from smib.slack.plugin_manager.loaders.abstract_plugin_loader import AbstractPluginLoader
from pathlib import Path
from injectable import injectable
import json
from smib.slack.plugin_manager import PluginMeta, PluginType, Plugin


@injectable(qualifier="PluginLoader")
class ShellPluginLoader(AbstractPluginLoader):
    type: PluginType = PluginType.SHELL
    id_file: Path = Path('plugin.json')

    def register_plugin(self, plugin: Plugin) -> Plugin:
        with open(plugin.directory / self.id_file) as f:
            plugin_file = json.load(f)

            plugin_meta = PluginMeta(
                name=plugin_file.get("name", plugin.id),
                description=plugin_file.get("description", None),
                author=plugin_file.get("author", None)
            )
            plugin.metadata = plugin_meta

        return plugin

    def unregister_plugin(self, plugin: Plugin) -> None:
        # Do nothing for shell - already handled by the base unload_plugin method
        pass
