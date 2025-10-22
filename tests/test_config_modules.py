import importlib
import types
import pytest

@pytest.mark.parametrize(
    "name",
    [
        "smib.config",
        "smib.config.general",
        "smib.config.project",
        "smib.config.database",
        "smib.config.logging_",
        "smib.config.webserver",
        "smib.config.slack",
        "smib.config._env_base_settings",
    ],
)
def test_config_modules_import(name: str):
    mod = importlib.import_module(name)
    assert isinstance(mod, types.ModuleType)
