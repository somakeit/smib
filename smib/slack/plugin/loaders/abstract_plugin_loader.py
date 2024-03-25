import inspect
from pathlib import Path
from abc import ABC, abstractmethod

from smib.common.config import PLUGINS_DIRECTORY
from slack_bolt import App
from smib.slack.plugin import PluginType, Plugin

from injectable import inject


class AbstractPluginLoader(ABC):

    plugins_directory: Path = PLUGINS_DIRECTORY
    type: PluginType
    id_file: Path

    @property
    @abstractmethod
    def type(self):
        pass

    @property
    @abstractmethod
    def id_file(self):
        pass

    @property
    def app(self):
        return inject(App)

    def load_all(self) -> list[Plugin]:
        plugins: list[Plugin] = []
        print(f"loading {self.type} plugins")
        for path in self.plugins_directory.glob(f'*/*/{self.id_file}'):
            plugins.append(self.load_plugin(path.parent))

        return plugins

    def plugin_path_to_id(self, plugin_path: Path) -> str:
        return plugin_path.relative_to(self.plugins_directory).as_posix().replace('/', '_')

    def create_plugin(self, plugin_path: Path) -> Plugin:
        return Plugin(
            type=self.type,
            directory=plugin_path,
            id=self.plugin_path_to_id(plugin_path),
            id_file=plugin_path / self.id_file,
            enabled=self.is_plugin_enabled(plugin_path),
            _base_directory=self.plugins_directory
        )

    def load_plugin(self, plugin_path: Path) -> Plugin:
        plugin = self.create_plugin(plugin_path)
        returned_plugin = self.register_plugin(plugin)
        if not plugin.enabled:
            self.unload_plugin(plugin)

        return returned_plugin

    def unload_plugin(self, plugin: Plugin) -> None:
        self.unregister_plugin(plugin)
        listeners = self.app._listeners[::]
        for listener in listeners:
            listener_path = inspect.getfile(listener.ack_function)
            if Path(listener_path).is_relative_to(plugin.directory):
                self.app._listeners.remove(listener)

    def reload_plugin(self, plugin: Plugin) -> Plugin:
        self.unload_plugin(plugin)
        reloaded_plugin = self.load_plugin(plugin.directory)
        return reloaded_plugin

    @staticmethod
    def is_plugin_enabled(plugin_path: Path) -> bool:
        return not (plugin_path / '.disable').exists()

    @abstractmethod
    def register_plugin(self, plugin: Plugin) -> Plugin:
        pass

    @abstractmethod
    def unregister_plugin(self, plugin: Plugin) -> None:
        pass