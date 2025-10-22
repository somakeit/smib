import importlib
import pkgutil
import types
import pytest

def iter_submodules(package: types.ModuleType):
    """Yield all submodule names under a package."""
    if not hasattr(package, "__path__"):
        return
    for modinfo in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        yield modinfo.name

@pytest.mark.parametrize("top_pkg_name", ["smib", "plugins"])
def test_top_packages_importable(top_pkg_name: str):
    pkg = importlib.import_module(top_pkg_name)
    assert isinstance(pkg, types.ModuleType)

@pytest.mark.parametrize("top_pkg_name", ["smib", "plugins"])
def test_all_submodules_importable(top_pkg_name: str):
    pkg = importlib.import_module(top_pkg_name)
    failures = []
    for fullname in iter_submodules(pkg):
        try:
            importlib.import_module(fullname)
        except Exception as exc:  # collect all failures to show at once
            failures.append((fullname, repr(exc)))
    if failures:
        messages = "\n".join(f"- {name}: {err}" for name, err in failures)
        pytest.fail(f"Failed to import {len(failures)} module(s):\n{messages}")
