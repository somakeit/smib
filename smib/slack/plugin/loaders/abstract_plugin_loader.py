import inspect
from pathlib import Path
from abc import ABC, abstractmethod
from pprint import pprint
from typing import List, Any

from apscheduler.job import Job

from smib.common.config import PLUGINS_DIRECTORY
from smib.slack.custom_app import CustomApp as App
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
        return inject("SlackApp")

    @property
    def scheduler(self):
        return inject("Scheduler")

    def load_all(self) -> list[Plugin]:
        plugins: list[Plugin] = []
        print(f"loading {self.type} plugins")
        for path in self.plugins_directory.glob(f'*/*/{self.id_file}'):
            plugin = self.load_plugin(path.parent)

            loaded_plugin_ids = {loaded_plugin.id for loaded_plugin in plugins}
            loaded_plugin_ids.update({loaded_plugin.id for loaded_plugin in inject("PluginManager")})

            # If the plugin ID already exists, give it a new one
            if plugin.id in loaded_plugin_ids:
                plugin.id = f"{plugin.id}_{id(plugin)}"

            plugins.append(plugin)

        return plugins

    def plugin_path_to_id(self, plugin_path: Path) -> str:
        return plugin_path.relative_to(self.plugins_directory).as_posix().replace('/', '_')

    def create_plugin(self, plugin_path: Path) -> Plugin:
        return Plugin(
            type=self.type,
            group=plugin_path.parent.name,
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
        self._remove_scheduled_jobs(plugin)
        self._remove_listeners(plugin)
        self._remove_middlewares(plugin)

    def _remove_listeners(self, plugin: Plugin) -> None:
        listeners = self.app._listeners[::]
        for listener in listeners:
            listener_path = inspect.getfile(inspect.unwrap(listener.ack_function))
            if Path(listener_path).is_relative_to(plugin.directory):
                self.app._listeners.remove(listener)

    def _remove_scheduled_jobs(self, plugin: Plugin) -> None:
        listeners = self.app._listeners[::]
        for listener in listeners:
            raw_listener_ack = inspect.unwrap(listener.ack_function)
            listener_path = inspect.getfile(raw_listener_ack)

            if not Path(listener_path).is_relative_to(plugin.directory):
                continue

            if job := self._find_job_from_plugin_function(raw_listener_ack):
                self.scheduler.remove_job(job.id)

    def _find_job_from_plugin_function(self, plugin_function: callable) -> Job:
        return next(iter(
            filter(
                lambda job: job.kwargs.get("_plugin_function", None) == plugin_function, self.scheduler.get_jobs()
            )), None)

    def _remove_middlewares(self, plugin: Plugin) -> None:
        middlewares = self.app._middleware_list[::]
        for middleware in middlewares:
            func = getattr(middleware, 'func', None)
            if not func:
                continue

            middleware_path = inspect.getfile(inspect.unwrap(func))
            if Path(middleware_path).is_relative_to(plugin.directory):
                self.app._middleware_list.remove(middleware)

    def reload_plugin(self, plugin: Plugin) -> Plugin:
        print(f"Reloading: {plugin}")
        self.unload_plugin(plugin)
        # print(self.scheduler.get_jobs())
        reloaded_plugin = self.load_plugin(plugin.directory)
        return reloaded_plugin

    @staticmethod
    def is_plugin_enabled(plugin_path: Path) -> bool:
        return not (plugin_path / '.disable').exists()

    @abstractmethod
    def register_plugin(self, plugin: Plugin) -> Plugin:
        ...

    @abstractmethod
    def unregister_plugin(self, plugin: Plugin) -> None:
        ...
