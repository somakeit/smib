import sys
from smib.slack.plugin_manager.loaders.abstract_plugin_loader import AbstractPluginLoader
from pathlib import Path
from injectable import injectable
import importlib
from smib.slack.plugin_manager import PluginMeta, PluginType, Plugin
from smib.common.config import ROOT_DIRECTORY


@injectable(primary=True, qualifier="PluginLoader")
class PythonPluginLoader(AbstractPluginLoader):
    type: PluginType = PluginType.PYTHON
    id_file: Path = Path('__init__.py')

    def register_plugin(self, plugin: Plugin) -> Plugin:
        module_path = self.plugin_path_to_module_path(plugin.directory)
        try:
            module = importlib.import_module(module_path)
        except Exception as e:
            module = None
            plugin.enabled = False
            plugin.error = f"{e.__class__.__name__}: {e}"
        else:
            plugin_meta = PluginMeta(
                name=getattr(module, '__plugin_name__', plugin.id),
                description=getattr(module, '__description__', None),
                author=getattr(module, '__author__', None)
            )
            plugin.metadata = plugin_meta

        return plugin

    @staticmethod
    def plugin_path_to_module_path(plugin_path: Path) -> str:
        return plugin_path.relative_to(ROOT_DIRECTORY.parent).as_posix().replace('/', '.')

    def unregister_plugin(self, plugin: Plugin) -> None:
        sys.modules.pop(self.plugin_path_to_module_path(plugin.directory), None)
