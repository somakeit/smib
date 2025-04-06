import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from smib.utilities.package import (
    get_package_root,
    get_package_version,
    get_actual_module_name,
    get_module_from_name,
)
import sys
import importlib.metadata

### Test: get_package_root ###
def test_get_package_root_found():
    """Test get_package_root with a valid package."""
    with patch("importlib.util.find_spec") as mock_find_spec:
        # Mock spec with submodule_search_locations
        mock_find_spec.return_value = MagicMock(submodule_search_locations=["/usr/lib/python3.12/os"])
        root_path = get_package_root("os")
        assert root_path == Path("/usr/lib/python3.12/os")
        mock_find_spec.assert_called_once_with("os")


def test_get_package_root_not_found():
    """Test get_package_root raises ImportError if the package cannot be found."""
    with patch("importlib.util.find_spec", return_value=None):  # Simulate missing package
        with pytest.raises(ImportError, match="Package 'missing_package' not found"):
            get_package_root("missing_package")


def test_get_package_root_no_search_locations():
    """Test get_package_root raises ImportError if no submodule_search_locations exist."""
    with patch("importlib.util.find_spec") as mock_find_spec:
        # Simulate a spec with no submodule_search_locations
        mock_find_spec.return_value = MagicMock(submodule_search_locations=None)
        with pytest.raises(ImportError, match="Could not determine root for package 'os'"):
            get_package_root("os")


### Test: get_package_version ###
def test_get_package_version_valid():
    """Test get_package_version with a valid package."""
    # Use the real `os` module for testing
    with patch("smib.utilities.package.version") as mock_version:
        mock_version.return_value = "1.0.0"  # Mocked version for `os`
        result = get_package_version("os")  # Call function
        assert result == "1.0.0"  # Verify the return
        mock_version.assert_called_once_with("os")  # Ensure mock was used


def test_get_package_version_invalid():
    """Test get_package_version raises PackageNotFoundError when the package doesn't exist."""
    # Simulate a package that doesn't exist
    with patch("smib.utilities.package.version", side_effect=importlib.metadata.PackageNotFoundError):
        with pytest.raises(importlib.metadata.PackageNotFoundError):
            get_package_version("missing_package")


### Test: get_actual_module_name ###
def test_get_actual_module_name_init_file():
    """Test get_actual_module_name with module file set to __init__.py."""
    mock_module = MagicMock()
    mock_module.__file__ = "/usr/lib/python3.12/os/__init__.py"
    module_name = get_actual_module_name(mock_module)
    assert module_name == "os"


def test_get_actual_module_name_regular_file():
    """Test get_actual_module_name with a regular module file."""
    mock_module = MagicMock()
    mock_module.__file__ = "/usr/lib/python3.12/os/path.py"
    module_name = get_actual_module_name(mock_module)
    assert module_name == "path"


### Test: get_module_from_name ###
def test_get_module_from_name_existing_module():
    """Test get_module_from_name retrieves an existing module from sys.modules."""
    # Use the real `os` module for this test
    module = get_module_from_name("os")
    assert module == sys.modules["os"]  # Ensure it matches sys.modules entry


def test_get_module_from_name_missing_module():
    """Test get_module_from_name raises KeyError when the module isn't loaded."""
    with pytest.raises(KeyError, match="non_existent_module"):
        get_module_from_name("non_existent_module")
