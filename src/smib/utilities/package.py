from pathlib import Path
from types import ModuleType


def get_package_root() -> Path:
    """ Returns the smib package root directory """
    import smib
    return Path(smib.__file__).parent

def get_actual_module_name(module: ModuleType) -> str:
    module_path = Path(module.__file__)
    if module_path.name == "__init__.py":
        return module_path.parent.name
    else:
        return module_path.with_suffix("").name
