import traceback

from smib.slack.plugin_manager.loaders import AbstractPluginLoader
from pathlib import Path
from injectable import injectable
import importlib
from smib.common.config import ROOT_DIRECTORY


@injectable
class PythonPluginLoader(AbstractPluginLoader):
    def load_from_directory(self, directory: Path):
        for plugin in directory.rglob('__init__.py'):
            self.load_plugin(plugin)

    def load_plugin(self, plugin):
        package_name = plugin.relative_to(ROOT_DIRECTORY.parent).parent.as_posix().replace('/', '.')
        try:
            module = importlib.import_module(package_name)
        except Exception as e:
            print(traceback.format_exception_only(e))
        else:
            plugin_name = getattr(module, '__plugin_name__', None)
            plugin_description = getattr(module, '__description__', None)
            plugin_author = getattr(module, '__author__', None)

            print(f"{plugin_name} ({plugin_description}) by {plugin_author}")
