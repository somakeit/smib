import os
from pathlib import Path
from typing import Iterator

from smib.slack.plugin.plugin import Plugin

from injectable import inject, inject_multiple, injectable, autowired, Autowired
from slack_bolt import App


@injectable(singleton=True, qualifier="PluginManager")
class PluginManager:
    @autowired
    def __init__(self, app: Autowired(App)):
        self.app = app
        self.plugins = []
        self.plugin_loaders = inject_multiple("PluginLoader", lazy=True)

    def load_all_plugins(self):
        for loader in self.plugin_loaders:
            self.plugins += loader.load_all()

    def reload_all_plugins(self):
        for loader in self.plugin_loaders:
            loader_plugins = [plugin for plugin in self.plugins if loader.type == plugin.type]
            for plugin in loader_plugins:
                self.plugins.remove(plugin)
                reloaded_plugin = loader.reload_plugin(plugin)
                self.plugins.append(reloaded_plugin)

    def disable_plugin(self, plugin: Plugin):
        loader = next((x for x in self.plugin_loaders if x.type == plugin.type), None)
        if not loader:
            return

        open(plugin.directory / '.disable', "wb")
        self.plugins.remove(plugin)

        reloaded_plugin = loader.reload_plugin(plugin)
        self.plugins.append(reloaded_plugin)

    def enable_plugin(self, plugin: Plugin):
        loader = next((x for x in self.plugin_loaders if x.type == plugin.type), None)
        if not loader:
            return

        if (disable_file := plugin.directory / '.disable').exists():
            os.remove(disable_file)

        self.plugins.remove(plugin)

        reloaded_plugin = loader.reload_plugin(plugin)
        self.plugins.append(reloaded_plugin)

    def get_plugin_from_file(self, file: Path) -> Plugin:
        return next((plugin for plugin in self.plugins if file.is_relative_to(plugin.directory)), None)

    def __iter__(self) -> Iterator[Plugin]:
        yield from self.plugins

