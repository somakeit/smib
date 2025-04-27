import importlib
import importlib.util
import uuid
from enum import StrEnum
from pathlib import Path
import sys
from types import ModuleType

import logging


class PluginModuleFormat(StrEnum):
    MODULE = 'module'
    PACKAGE = 'package'


logger = logging.getLogger(__name__)

def module_exists_by_name(module_name: str) -> bool:
    return module_name in sys.modules


def import_module_from_path(module_path: Path, module_name: str | None = None) -> ModuleType:
    module_path = module_path.resolve()
    # unique_suffix = str(uuid.uuid4()).replace("-", "")
    # module_name = module_name or f"{module_path.with_suffix('').name}_{unique_suffix}"
    module_name = module_name or module_path.with_suffix('').name

    # Ensure the module is a .py file
    if not module_path.suffix == ".py":
        raise ImportError(f"Module is not a python (.py) file {module_path}")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Failed to create module spec for {module_path}")

    module = importlib.util.module_from_spec(spec)

    if module_exists_by_name(module_name):
        raise ImportError(f"Module {module_name} already exists")

    sys.modules[module_name] = module

    if spec.loader is None:
        raise ImportError(f"Module loader is None for {module_path}")

    spec.loader.exec_module(module)

    return module

def import_package_from_path(package_path: Path, package_name: str | None = None) -> ModuleType:
    package_path = package_path.resolve()
    # unique_suffix = str(uuid.uuid4()).replace("-", "")
    # package_name = package_name or f"{package_path.name}_{unique_suffix}"
    package_name = package_name or package_path.name

    # Ensure the package contains an __init__.py file
    init_file = package_path / '__init__.py'
    if not init_file.exists():
        raise ImportError(f"Cannot find __init__.py in package directory {package_path}")

    # Add the package path to sys.path to ensure all submodules can be imported
    sys.path.insert(0, str(package_path.parent))

    # Load the package
    spec = importlib.util.spec_from_file_location(package_name, init_file)
    if spec is None:
        raise ImportError(f"Failed to create module spec for {init_file}")

    package = importlib.util.module_from_spec(spec)

    if module_exists_by_name(package_name):
        raise ImportError(f"Module {package_name} already exists")

    sys.modules[package_name] = package

    if spec.loader is None:
        raise ImportError(f"Module loader is None for {init_file}")

    spec.loader.exec_module(package)

    # Remove the package path from sys.path
    sys.path.pop(0)

    return package

def import_from_path(module_path: Path | str) -> ModuleType:
    if isinstance(module_path, str):
        module_path = Path(module_path)

    path = module_path.resolve()

    if not path.exists():
        raise FileNotFoundError(f"No such file or directory: '{path}'")

    if path.is_dir():
        return import_package_from_path(path)
    elif path.is_file():
        return import_module_from_path(path)
    else:
        raise ImportError(f"Cannot import from '{path}': unknown type")

def import_all_from_directory(directory_path: Path | str) -> list[ModuleType]:
    if isinstance(directory_path, str):
        directory_path = Path(directory_path)

    directory = directory_path.resolve()

    if not directory.is_dir():
        raise NotADirectoryError(f"{directory_path} is not a directory")

    imported_modules = []

    for item in directory.iterdir():
        if item.name == '__init__.py':
            continue
        try:
            # Import module or package if it's a .py file or a directory with __init__.py file
            if item.is_file() and item.suffix == '.py':
                imported_modules.append(import_from_path(str(item)))
            elif item.is_dir() and (item / '__init__.py').exists():
                imported_modules.append(import_from_path(str(item)))
        except (ImportError, FileNotFoundError) as e:
            logger.exception(item, exc_info=e)
        except Exception as e:
            logger.exception(item, exc_info=e)

    return imported_modules
