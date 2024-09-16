import importlib.util
import sys
from os import PathLike
from pathlib import Path
from types import ModuleType

from smib.config import PLUGIN_DIRECTORY
from smib.utils import get_root_path


def load_plugins(directory: PathLike | None = None) -> None:
    directory = directory or get_root_path() / PLUGIN_DIRECTORY

    # Ensure the directory is a string path and is first in sys.path
    directory_str = str(directory)
    if directory_str not in sys.path:
        sys.path.insert(0, directory_str)  # Insert at the beginning

    for plugin_id_file in directory.glob('*/__init__.py'):
        if not plugin_id_file.is_file():
            continue

        plugin_name: str = plugin_id_file.parent.name
        module: ModuleType | None = None

        if plugin_name in sys.modules:
            plugin_name = f"smib_plugin_{plugin_name}"

        try:
            # Load the module directly from the file path
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_id_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[plugin_name] = module
                spec.loader.exec_module(module)
            else:
                raise ImportError(f"Cannot find spec for module {plugin_name}")
        except Exception as e:
            print(f"Exception when importing plugin {plugin_name}\n{type(e).__name__}: {e}")
            continue
        else:
            print(f"Successfully imported plugin {plugin_name}")

        if module is None:
            continue

        plugin_setup = getattr(module, 'setup', None)
        if callable(plugin_setup):
            try:
                plugin_setup()
            except Exception as e:
                print(f"Exception when running setup for plugin {plugin_name}\n{type(e).__name__}: {e}")
        else:
            print(f"Plugin {plugin_name} has no setup function!")

def list_imported_plugins(directory: PathLike | None = None) -> None:
    directory = directory or get_root_path() / PLUGIN_DIRECTORY
    for module_name, module in sys.modules.items():
        if getattr(module, '__file__', None) is None:
            continue

        if Path(module.__file__).is_relative_to(directory):
            print(module_name)

if __name__ == '__main__':
    load_plugins()
    list_imported_plugins()