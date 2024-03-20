from injectable import inject, inject_multiple, injectable
from smib.common.config import PLUGINS_DIRECTORY, ROOT_DIRECTORY
from smib.slack.plugin_manager.loaders import AbstractPluginLoader
from pathlib import Path


@injectable(singleton=True, qualifier="PluginManager")
class PluginManager:
    def __init__(self, plugins_dir: str | Path = None):
        self.plugins = []
        self.plugins_dir = Path(plugins_dir) if plugins_dir else Path(PLUGINS_DIRECTORY)
        self.plugin_loaders = inject_multiple(AbstractPluginLoader)

    def load_all_plugins(self):
        for loader in self.plugin_loaders:
            loader.set_plugin_manager(self)
            loader.load_from_directory(self.plugins_dir)
