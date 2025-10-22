import importlib
import types
import pytest

@pytest.mark.parametrize(
    "name",
    [
        "smib.error_handler",
        "smib.signal_handler",
        # Add more leaf modules here as you grow the suite.
    ],
)
def test_leaf_modules_import(name: str):
    mod = importlib.import_module(name)
    assert isinstance(mod, types.ModuleType)
