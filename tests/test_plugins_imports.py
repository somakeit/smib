import importlib
import types
import pytest

@pytest.mark.parametrize(
    "name",
    [
        "plugins.core",
        "plugins.core.core",
        "plugins.core.core.models",
        "plugins.core.static",
        "plugins.core.api_docs",
        "plugins.space",  # presence of package
    ],
)
def test_plugins_imports(name: str):
    mod = importlib.import_module(name)
    assert isinstance(mod, types.ModuleType)
