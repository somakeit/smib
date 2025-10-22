import importlib
import types

def test_smib_package_root_imports():
    smib = importlib.import_module("smib")
    assert isinstance(smib, types.ModuleType)

def test_smib_has_subpackages_we_expect():
    # Validate core subpackages are present and importable.
    subpackages = [
        "smib.config",
        "smib.events",
        "smib.events.handlers",
        "smib.events.services",
        "smib.events.responses",
        "smib.events.interfaces",
        "smib.events.middlewares",
        "smib.utilities",
        "smib.logging_",
        "smib.plugins",
        "smib.db",
    ]
    for name in subpackages:
        mod = importlib.import_module(name)
        assert isinstance(mod, types.ModuleType), f"{name} should import"

def test_smib_main_module_imports():
    # Import only; do not execute any main/runner code.
    mod = importlib.import_module("smib.__main__")
    assert isinstance(mod, types.ModuleType)
