import os
from pathlib import Path
from typing import Iterator

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from smib.slack.plugin import PluginType
    from smib.slack.plugin.loaders.abstract_plugin_loader import AbstractPluginLoader
from smib.slack.plugin.plugin import Plugin

from injectable import inject, inject_multiple, injectable, autowired, Autowired
from smib.slack.custom_app import CustomApp as App


@injectable(singleton=True, qualifier="PluginManager")
class PluginManager:
    @autowired
    def __init__(self, app: Autowired("SlackApp")):
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
        logger = inject("logger")

        logger.info(f"Disabling plugin {plugin.id}")

        loader = self._get_plugin_loader_from_type(plugin.type)
        if not loader:
            logger.warning(f"Unable to disable plugin {plugin.id} - no loader found")
            return

        open(plugin.directory / '.disable', "wb")
        self.plugins.remove(plugin)

        reloaded_plugin = loader.reload_plugin(plugin)
        self.plugins.append(reloaded_plugin)

        logger.info(f"Plugin {plugin.id} disabled")

    def enable_plugin(self, plugin: Plugin):
        logger = inject("logger")

        logger.info(f"Enabling plugin {plugin.id}")

        loader = self._get_plugin_loader_from_type(plugin.type)
        if not loader:
            logger.warning(f"Unable to enable plugin {plugin.id} - no loader found")
            return

        if (disable_file := plugin.directory / '.disable').exists():
            os.remove(disable_file)
        else:
            logger.debug(f"Plugin {plugin.id} already enabled! Reloading anyway...")

        self.plugins.remove(plugin)

        reloaded_plugin = loader.reload_plugin(plugin)
        self.plugins.append(reloaded_plugin)

        logger.info(f"Plugin {plugin.id} enabled")

    def get_plugin_from_file(self, file: Path) -> Plugin:
        return next((plugin for plugin in self.plugins if file.is_relative_to(plugin.directory)), None)

    def __iter__(self) -> Iterator[Plugin]:
        yield from self.plugins

    def _get_plugin_loader_from_type(self, plugin_type: "PluginType") -> "AbstractPluginLoader":
        loader = next((x for x in self.plugin_loaders if x.type == plugin_type), None)
        return loader

