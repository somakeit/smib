import sys
from pathlib import Path
from types import ModuleType
import importlib.util
from importlib.metadata import version


def get_package_root(package_name: str) -> Path:
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        raise ImportError(f"Package '{package_name}' not found")

    if spec.submodule_search_locations:
        return Path(next(iter(spec.submodule_search_locations)))
    else:
        raise ImportError(f"Could not determine root for package '{package_name}'")

def get_package_version(package_name: str):
    return version(package_name)

def get_actual_module_name(module: ModuleType) -> str:
    module_path = Path(module.__file__)
    if module_path.name == "__init__.py":
        return module_path.parent.name
    else:
        return module_path.with_suffix("").name

def get_module_from_name(module_name: str):
    return sys.modules[module_name]

