from abc import ABC, abstractmethod
from pathlib import Path
from injectable import Autowired, autowired, injectable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from smib.slack.plugin_manager.manager import PluginManager


class AbstractPluginLoader(ABC):

    plugin_manager: "PluginManager" = None

    def set_plugin_manager(self, plugin_manager: "PluginManager"):
        self.plugin_manager = plugin_manager

    @abstractmethod
    def load_from_directory(self, directory: Path):
        pass
