import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import sys
import importlib.util
from enum import StrEnum

from smib.plugins import (
    PluginModuleFormat,
    module_exists_by_name,
    import_module_from_path,
    import_package_from_path,
    import_from_path,
    import_all_from_directory
)


### Test: PluginModuleFormat Enum ###
def test_plugin_module_format_enum():
    """Test PluginModuleFormat enum values."""
    # Verify PluginModuleFormat is a StrEnum
    assert issubclass(PluginModuleFormat, StrEnum)

    # Verify enum values
    assert PluginModuleFormat.MODULE == 'module'
    assert PluginModuleFormat.PACKAGE == 'package'

    # Verify enum members
    assert len(PluginModuleFormat) == 2
    assert PluginModuleFormat.MODULE in PluginModuleFormat
    assert PluginModuleFormat.PACKAGE in PluginModuleFormat

    # Verify string comparison works
    assert PluginModuleFormat.MODULE == 'module'
    assert 'module' == PluginModuleFormat.MODULE
    assert PluginModuleFormat.PACKAGE == 'package'
    assert 'package' == PluginModuleFormat.PACKAGE


### Test: module_exists_by_name ###
def test_module_exists_by_name():
    """Test module_exists_by_name function."""
    # Test with existing module
    assert module_exists_by_name('sys') is True

    # Test with non-existent module
    assert module_exists_by_name('non_existent_module_name') is False


### Test: import_module_from_path ###
@patch('smib.plugins.importlib.util.spec_from_file_location')
@patch('smib.plugins.importlib.util.module_from_spec')
@patch('smib.plugins.module_exists_by_name')
def test_import_module_from_path(mock_module_exists, mock_module_from_spec, mock_spec_from_file_location):
    """Test import_module_from_path function."""
    # Setup mocks
    mock_path = MagicMock(spec=Path)
    mock_path.resolve.return_value = mock_path
    mock_path.suffix = '.py'
    mock_path.with_suffix.return_value.name = 'test_module'

    mock_spec = MagicMock()
    mock_spec_from_file_location.return_value = mock_spec

    mock_module = MagicMock()
    mock_module_from_spec.return_value = mock_module

    mock_module_exists.return_value = False

    # Call function
    result = import_module_from_path(mock_path)

    # Verify results
    assert result == mock_module
    mock_path.resolve.assert_called_once()
    mock_spec_from_file_location.assert_called_once_with('test_module', mock_path)
    mock_module_from_spec.assert_called_once_with(mock_spec)
    mock_module_exists.assert_called_once_with('test_module')
    assert 'test_module' in sys.modules
    mock_spec.loader.exec_module.assert_called_once_with(mock_module)

    # Clean up
    if 'test_module' in sys.modules:
        del sys.modules['test_module']


def test_import_module_from_path_with_custom_name():
    """Test import_module_from_path function with custom module name."""
    # Setup mocks
    with patch('smib.plugins.importlib.util.spec_from_file_location') as mock_spec_from_file_location, \
         patch('smib.plugins.importlib.util.module_from_spec') as mock_module_from_spec, \
         patch('smib.plugins.module_exists_by_name') as mock_module_exists:

        mock_path = MagicMock(spec=Path)
        mock_path.resolve.return_value = mock_path
        mock_path.suffix = '.py'

        mock_spec = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec

        mock_module = MagicMock()
        mock_module_from_spec.return_value = mock_module

        mock_module_exists.return_value = False

        # Call function with custom name
        result = import_module_from_path(mock_path, module_name='custom_module_name')

        # Verify results
        assert result == mock_module
        mock_path.resolve.assert_called_once()
        mock_spec_from_file_location.assert_called_once_with('custom_module_name', mock_path)
        mock_module_from_spec.assert_called_once_with(mock_spec)
        mock_module_exists.assert_called_once_with('custom_module_name')
        assert 'custom_module_name' in sys.modules
        mock_spec.loader.exec_module.assert_called_once_with(mock_module)

        # Clean up
        if 'custom_module_name' in sys.modules:
            del sys.modules['custom_module_name']


def test_import_module_from_path_not_py_file():
    """Test import_module_from_path raises ImportError when file is not a .py file."""
    # Setup mocks
    mock_path = MagicMock(spec=Path)
    mock_path.resolve.return_value = mock_path
    mock_path.suffix = '.txt'

    # Call function and verify it raises ImportError
    with pytest.raises(ImportError, match=r"Module is not a python \(.py\) file"):
        import_module_from_path(mock_path)


def test_import_module_from_path_module_exists():
    """Test import_module_from_path raises ImportError when module already exists."""
    # Setup mocks
    with patch('smib.plugins.module_exists_by_name') as mock_module_exists, \
         patch('smib.plugins.importlib.util.spec_from_file_location') as mock_spec_from_file_location:

        mock_path = MagicMock(spec=Path)
        mock_path.resolve.return_value = mock_path
        mock_path.suffix = '.py'
        mock_path.with_suffix.return_value.name = 'existing_module'

        # Mock spec_from_file_location to return a valid spec
        mock_spec = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec

        mock_module_exists.return_value = True

        # Call function and verify it raises ImportError
        with pytest.raises(ImportError, match=r"Module existing_module already exists"):
            import_module_from_path(mock_path)


### Test: import_package_from_path ###
@patch('smib.plugins.importlib.util.spec_from_file_location')
@patch('smib.plugins.importlib.util.module_from_spec')
@patch('smib.plugins.module_exists_by_name')
@patch('smib.plugins.sys.path')
def test_import_package_from_path(mock_sys_path, mock_module_exists, mock_module_from_spec, mock_spec_from_file_location):
    """Test import_package_from_path function."""
    # Setup mocks
    mock_package_path = MagicMock(spec=Path)
    mock_package_path.resolve.return_value = mock_package_path
    mock_package_path.name = 'test_package'
    mock_package_path.__truediv__.return_value.exists.return_value = True
    mock_package_path.parent = '/path/to/parent'

    mock_init_file = MagicMock(spec=Path)
    mock_package_path.__truediv__.return_value = mock_init_file

    mock_spec = MagicMock()
    mock_spec_from_file_location.return_value = mock_spec

    mock_package = MagicMock()
    mock_module_from_spec.return_value = mock_package

    mock_module_exists.return_value = False

    # Call function
    result = import_package_from_path(mock_package_path)

    # Verify results
    assert result == mock_package
    mock_package_path.resolve.assert_called_once()
    mock_package_path.__truediv__.assert_called_once_with('__init__.py')
    mock_init_file.exists.assert_called_once()
    mock_sys_path.insert.assert_called_once_with(0, str(mock_package_path.parent))
    mock_spec_from_file_location.assert_called_once_with('test_package', mock_init_file)
    mock_module_from_spec.assert_called_once_with(mock_spec)
    mock_module_exists.assert_called_once_with('test_package')
    assert 'test_package' in sys.modules
    mock_spec.loader.exec_module.assert_called_once_with(mock_package)
    mock_sys_path.pop.assert_called_once_with(0)

    # Clean up
    if 'test_package' in sys.modules:
        del sys.modules['test_package']


def test_import_package_from_path_with_custom_name():
    """Test import_package_from_path function with custom package name."""
    # Setup mocks
    with patch('smib.plugins.importlib.util.spec_from_file_location') as mock_spec_from_file_location, \
         patch('smib.plugins.importlib.util.module_from_spec') as mock_module_from_spec, \
         patch('smib.plugins.module_exists_by_name') as mock_module_exists, \
         patch('smib.plugins.sys.path') as mock_sys_path:

        mock_package_path = MagicMock(spec=Path)
        mock_package_path.resolve.return_value = mock_package_path
        mock_package_path.__truediv__.return_value.exists.return_value = True
        mock_package_path.parent = '/path/to/parent'

        mock_init_file = MagicMock(spec=Path)
        mock_package_path.__truediv__.return_value = mock_init_file

        mock_spec = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec

        mock_package = MagicMock()
        mock_module_from_spec.return_value = mock_package

        mock_module_exists.return_value = False

        # Call function with custom name
        result = import_package_from_path(mock_package_path, package_name='custom_package_name')

        # Verify results
        assert result == mock_package
        mock_package_path.resolve.assert_called_once()
        mock_package_path.__truediv__.assert_called_once_with('__init__.py')
        mock_init_file.exists.assert_called_once()
        mock_sys_path.insert.assert_called_once_with(0, str(mock_package_path.parent))
        mock_spec_from_file_location.assert_called_once_with('custom_package_name', mock_init_file)
        mock_module_from_spec.assert_called_once_with(mock_spec)
        mock_module_exists.assert_called_once_with('custom_package_name')
        assert 'custom_package_name' in sys.modules
        mock_spec.loader.exec_module.assert_called_once_with(mock_package)
        mock_sys_path.pop.assert_called_once_with(0)

        # Clean up
        if 'custom_package_name' in sys.modules:
            del sys.modules['custom_package_name']


def test_import_package_from_path_no_init_file():
    """Test import_package_from_path raises ImportError when __init__.py is missing."""
    # Setup mocks
    mock_package_path = MagicMock(spec=Path)
    mock_package_path.resolve.return_value = mock_package_path
    mock_package_path.name = 'test_package'
    mock_package_path.__truediv__.return_value.exists.return_value = False

    # Call function and verify it raises ImportError
    with pytest.raises(ImportError, match=r"Cannot find __init__.py in package directory"):
        import_package_from_path(mock_package_path)


def test_import_package_from_path_module_exists():
    """Test import_package_from_path raises ImportError when package already exists."""
    # Setup mocks
    with patch('smib.plugins.module_exists_by_name') as mock_module_exists, \
         patch('smib.plugins.importlib.util.spec_from_file_location') as mock_spec_from_file_location, \
         patch('smib.plugins.sys.path') as mock_sys_path:

        mock_package_path = MagicMock(spec=Path)
        mock_package_path.resolve.return_value = mock_package_path
        mock_package_path.name = 'existing_package'
        mock_package_path.__truediv__.return_value.exists.return_value = True
        mock_package_path.parent = '/path/to/parent'

        # Mock spec_from_file_location to return a valid spec
        mock_spec = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec

        mock_module_exists.return_value = True

        # Call function and verify it raises ImportError
        with pytest.raises(ImportError, match=r"Module existing_package already exists"):
            import_package_from_path(mock_package_path)


### Test: import_from_path ###
@patch('smib.plugins.import_package_from_path')
@patch('smib.plugins.import_module_from_path')
def test_import_from_path_with_file(mock_import_module, mock_import_package):
    """Test import_from_path function with a file path."""
    # Setup mocks
    mock_path = MagicMock(spec=Path)
    mock_path.resolve.return_value = mock_path
    mock_path.exists.return_value = True
    mock_path.is_dir.return_value = False
    mock_path.is_file.return_value = True

    mock_module = MagicMock()
    mock_import_module.return_value = mock_module

    # Call function
    result = import_from_path(mock_path)

    # Verify results
    assert result == mock_module
    mock_path.resolve.assert_called_once()
    mock_path.exists.assert_called_once()
    mock_path.is_dir.assert_called_once()
    mock_path.is_file.assert_called_once()
    mock_import_module.assert_called_once_with(mock_path)
    mock_import_package.assert_not_called()


@patch('smib.plugins.import_package_from_path')
@patch('smib.plugins.import_module_from_path')
def test_import_from_path_with_directory(mock_import_module, mock_import_package):
    """Test import_from_path function with a directory path."""
    # Setup mocks
    mock_path = MagicMock(spec=Path)
    mock_path.resolve.return_value = mock_path
    mock_path.exists.return_value = True
    mock_path.is_dir.return_value = True

    mock_package = MagicMock()
    mock_import_package.return_value = mock_package

    # Call function
    result = import_from_path(mock_path)

    # Verify results
    assert result == mock_package
    mock_path.resolve.assert_called_once()
    mock_path.exists.assert_called_once()
    mock_path.is_dir.assert_called_once()
    mock_import_package.assert_called_once_with(mock_path)
    mock_import_module.assert_not_called()


@patch('smib.plugins.Path')
@patch('smib.plugins.import_package_from_path')
@patch('smib.plugins.import_module_from_path')
def test_import_from_path_with_string(mock_import_module, mock_import_package, mock_path_class):
    """Test import_from_path function with a string path."""
    # Setup mocks
    mock_path_obj = MagicMock(spec=Path)
    mock_path_class.return_value = mock_path_obj
    mock_path_obj.resolve.return_value = mock_path_obj
    mock_path_obj.exists.return_value = True
    mock_path_obj.is_dir.return_value = True

    mock_package = MagicMock()
    mock_import_package.return_value = mock_package

    # Call function
    result = import_from_path('/path/to/package')

    # Verify results
    assert result == mock_package
    mock_path_class.assert_called_once_with('/path/to/package')
    mock_path_obj.resolve.assert_called_once()
    mock_path_obj.exists.assert_called_once()
    mock_path_obj.is_dir.assert_called_once()
    mock_import_package.assert_called_once_with(mock_path_obj)
    mock_import_module.assert_not_called()


def test_import_from_path_not_exists():
    """Test import_from_path raises FileNotFoundError when path doesn't exist."""
    # Setup mocks
    mock_path = MagicMock(spec=Path)
    mock_path.resolve.return_value = mock_path
    mock_path.exists.return_value = False

    # Call function and verify it raises FileNotFoundError
    with pytest.raises(FileNotFoundError, match=r"No such file or directory:"):
        import_from_path(mock_path)


def test_import_from_path_unknown_type():
    """Test import_from_path raises ImportError for unknown path type."""
    # Setup mocks
    mock_path = MagicMock(spec=Path)
    mock_path.resolve.return_value = mock_path
    mock_path.exists.return_value = True
    mock_path.is_dir.return_value = False
    mock_path.is_file.return_value = False

    # Call function and verify it raises ImportError
    with pytest.raises(ImportError, match=r"Cannot import from .* unknown type"):
        import_from_path(mock_path)


### Test: import_all_from_directory ###
@patch('smib.plugins.import_from_path')
@patch('smib.plugins.logger')
def test_import_all_from_directory(mock_logger, mock_import_from_path):
    """Test import_all_from_directory function."""
    # Setup mocks
    mock_directory = MagicMock(spec=Path)
    mock_directory.resolve.return_value = mock_directory
    mock_directory.is_dir.return_value = True

    # Create mock items in directory
    mock_file1 = MagicMock(spec=Path)
    mock_file1.name = 'module1.py'
    mock_file1.is_file.return_value = True
    mock_file1.suffix = '.py'

    mock_file2 = MagicMock(spec=Path)
    mock_file2.name = '__init__.py'  # Should be skipped
    mock_file2.is_file.return_value = True
    mock_file2.suffix = '.py'

    mock_file3 = MagicMock(spec=Path)
    mock_file3.name = 'not_python.txt'  # Should be skipped
    mock_file3.is_file.return_value = True
    mock_file3.suffix = '.txt'

    mock_dir1 = MagicMock(spec=Path)
    mock_dir1.name = 'package1'
    mock_dir1.is_file.return_value = False
    mock_dir1.is_dir.return_value = True
    mock_dir1.__truediv__.return_value.exists.return_value = True  # Has __init__.py

    mock_dir2 = MagicMock(spec=Path)
    mock_dir2.name = 'not_package'
    mock_dir2.is_file.return_value = False
    mock_dir2.is_dir.return_value = True
    mock_dir2.__truediv__.return_value.exists.return_value = False  # No __init__.py

    mock_directory.iterdir.return_value = [mock_file1, mock_file2, mock_file3, mock_dir1, mock_dir2]

    # Setup mock modules
    mock_module1 = MagicMock()
    mock_package1 = MagicMock()

    # Instead of using a lambda, we'll directly patch the implementation of import_all_from_directory
    # to control what gets added to the result list
    def mock_implementation(path):
        if str(path) == str(mock_file1):
            return mock_module1
        elif str(path) == str(mock_dir1):
            return mock_package1
        else:
            # For any other path, raise ImportError to simulate failure
            # This ensures these modules won't be added to the result list
            raise ImportError(f"Mock import error for {path}")

    mock_import_from_path.side_effect = mock_implementation

    # Call function
    result = import_all_from_directory(mock_directory)

    # Verify results
    assert len(result) == 2
    assert mock_module1 in result
    assert mock_package1 in result

    mock_directory.resolve.assert_called_once()
    mock_directory.is_dir.assert_called_once()
    mock_directory.iterdir.assert_called_once()

    # Verify import_from_path was called for module1.py and package1
    mock_import_from_path.assert_any_call(str(mock_file1))
    mock_import_from_path.assert_any_call(str(mock_dir1))


@patch('smib.plugins.Path')
@patch('smib.plugins.import_from_path')
def test_import_all_from_directory_with_string(mock_import_from_path, mock_path_class):
    """Test import_all_from_directory function with a string path."""
    # Setup mocks
    mock_directory = MagicMock(spec=Path)
    mock_path_class.return_value = mock_directory
    mock_directory.resolve.return_value = mock_directory
    mock_directory.is_dir.return_value = True

    # Create mock items in directory
    mock_file1 = MagicMock(spec=Path)
    mock_file1.name = 'module1.py'
    mock_file1.is_file.return_value = True
    mock_file1.suffix = '.py'

    mock_directory.iterdir.return_value = [mock_file1]

    # Setup mock modules
    mock_module1 = MagicMock()
    mock_import_from_path.return_value = mock_module1

    # Call function
    result = import_all_from_directory('/path/to/directory')

    # Verify results
    assert len(result) == 1
    assert mock_module1 in result

    mock_path_class.assert_called_once_with('/path/to/directory')
    mock_directory.resolve.assert_called_once()
    mock_directory.is_dir.assert_called_once()
    mock_directory.iterdir.assert_called_once()

    # Verify import_from_path was called for module1.py
    mock_import_from_path.assert_called_once_with(str(mock_file1))


def test_import_all_from_directory_not_a_directory():
    """Test import_all_from_directory raises NotADirectoryError when path is not a directory."""
    # Setup mocks
    mock_directory = MagicMock(spec=Path)
    mock_directory.resolve.return_value = mock_directory
    mock_directory.is_dir.return_value = False

    # Call function and verify it raises NotADirectoryError
    with pytest.raises(NotADirectoryError, match=r"is not a directory"):
        import_all_from_directory(mock_directory)


@patch('smib.plugins.logger')
@patch('smib.plugins.import_from_path')
def test_import_all_from_directory_with_import_error(mock_import_from_path, mock_logger):
    """Test import_all_from_directory handles ImportError."""
    # Setup mocks
    mock_directory = MagicMock(spec=Path)
    mock_directory.resolve.return_value = mock_directory
    mock_directory.is_dir.return_value = True

    # Create mock items in directory
    mock_file1 = MagicMock(spec=Path)
    mock_file1.name = 'module1.py'
    mock_file1.is_file.return_value = True
    mock_file1.suffix = '.py'

    mock_directory.iterdir.return_value = [mock_file1]

    # Setup mock to raise ImportError
    mock_import_from_path.side_effect = ImportError("Test import error")

    # Call function
    result = import_all_from_directory(mock_directory)

    # Verify results
    assert len(result) == 0
    mock_directory.resolve.assert_called_once()
    mock_directory.is_dir.assert_called_once()
    mock_directory.iterdir.assert_called_once()

    # Verify import_from_path was called and logger.exception was called
    mock_import_from_path.assert_called_once_with(str(mock_file1))
    mock_logger.exception.assert_called_once_with(mock_file1, exc_info=mock_import_from_path.side_effect)


@patch('smib.plugins.logger')
@patch('smib.plugins.import_from_path')
def test_import_all_from_directory_with_general_exception(mock_import_from_path, mock_logger):
    """Test import_all_from_directory handles general exceptions."""
    # Setup mocks
    mock_directory = MagicMock(spec=Path)
    mock_directory.resolve.return_value = mock_directory
    mock_directory.is_dir.return_value = True

    # Create mock items in directory
    mock_file1 = MagicMock(spec=Path)
    mock_file1.name = 'module1.py'
    mock_file1.is_file.return_value = True
    mock_file1.suffix = '.py'

    mock_directory.iterdir.return_value = [mock_file1]

    # Setup mock to raise a general exception
    mock_import_from_path.side_effect = Exception("Test general exception")

    # Call function
    result = import_all_from_directory(mock_directory)

    # Verify results
    assert len(result) == 0
    mock_directory.resolve.assert_called_once()
    mock_directory.is_dir.assert_called_once()
    mock_directory.iterdir.assert_called_once()

    # Verify import_from_path was called and logger.exception was called
    mock_import_from_path.assert_called_once_with(str(mock_file1))
    mock_logger.exception.assert_called_once_with(mock_file1, exc_info=mock_import_from_path.side_effect)
