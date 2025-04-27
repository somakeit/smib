import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import inspect
from types import ModuleType

from smib.plugins.lifecycle_manager import PluginLifecycleManager
from smib.plugins.locator import PluginLocator


@pytest.fixture
def mock_lifecycle_manager():
    """Fixture for a mocked PluginLifecycleManager."""
    mock_manager = MagicMock(spec=PluginLifecycleManager)
    mock_manager.plugin_map = []
    return mock_manager


@pytest.fixture
def plugin_locator(mock_lifecycle_manager):
    """Fixture for a PluginLocator instance."""
    return PluginLocator(mock_lifecycle_manager)


class TestPluginLocator:
    """Tests for the PluginLocator class."""

    def test_init(self, plugin_locator, mock_lifecycle_manager):
        """Test initialization of PluginLocator."""
        assert plugin_locator.lifecycle_manager == mock_lifecycle_manager

    def test_get_by_unique_name_found(self, plugin_locator):
        """Test get_by_unique_name when the plugin is found."""
        # Setup
        mock_module = MagicMock(spec=ModuleType)
        plugin_locator.lifecycle_manager.plugin_map = [
            {"unique_name": "test_plugin", "module": mock_module},
            {"unique_name": "other_plugin", "module": MagicMock()}
        ]

        # Execute
        result = plugin_locator.get_by_unique_name("test_plugin")

        # Verify
        assert result == mock_module

    def test_get_by_unique_name_not_found(self, plugin_locator):
        """Test get_by_unique_name when the plugin is not found."""
        # Setup
        plugin_locator.lifecycle_manager.plugin_map = [
            {"unique_name": "other_plugin", "module": MagicMock()}
        ]

        # Execute
        result = plugin_locator.get_by_unique_name("test_plugin")

        # Verify
        assert result is None

    def test_get_by_name_found(self, plugin_locator):
        """Test get_by_name when the plugin is found."""
        # Setup
        mock_module = MagicMock(spec=ModuleType)
        plugin_locator.lifecycle_manager.plugin_map = [
            {"name": "test_plugin", "module": mock_module},
            {"name": "other_plugin", "module": MagicMock()}
        ]

        # Execute
        result = plugin_locator.get_by_name("test_plugin")

        # Verify
        assert result == mock_module

    def test_get_by_name_not_found(self, plugin_locator):
        """Test get_by_name when the plugin is not found."""
        # Setup
        plugin_locator.lifecycle_manager.plugin_map = [
            {"name": "other_plugin", "module": MagicMock()}
        ]

        # Execute
        result = plugin_locator.get_by_name("test_plugin")

        # Verify
        assert result is None

    def test_get_by_path_found(self, plugin_locator):
        """Test get_by_path when the plugin is found."""
        # Setup
        mock_module = MagicMock(spec=ModuleType)
        mock_path = Path("/path/to/plugin")
        plugin_locator.lifecycle_manager.plugin_map = [
            {"path": mock_path, "module": mock_module},
            {"path": Path("/path/to/other"), "module": MagicMock()}
        ]

        # Execute
        result = plugin_locator.get_by_path(mock_path)

        # Verify
        assert result == mock_module

    def test_get_by_path_not_found(self, plugin_locator):
        """Test get_by_path when the plugin is not found."""
        # Setup
        plugin_locator.lifecycle_manager.plugin_map = [
            {"path": Path("/path/to/other"), "module": MagicMock()}
        ]

        # Execute
        result = plugin_locator.get_by_path(Path("/path/to/plugin"))

        # Verify
        assert result is None

    def test_get_name(self, plugin_locator):
        """Test get_name method."""
        # Setup
        mock_module = MagicMock(spec=ModuleType)

        # Mock get_actual_module_name
        with patch('smib.plugins.locator.get_actual_module_name') as mock_get_name:
            mock_get_name.return_value = "actual_module_name"

            # Execute
            result = plugin_locator.get_name(mock_module)

            # Verify
            assert result == "actual_module_name"
            mock_get_name.assert_called_once_with(mock_module)

    def test_get_unique_name(self, plugin_locator):
        """Test get_unique_name method."""
        # Setup
        mock_module = MagicMock(spec=ModuleType)
        mock_module.__name__ = "test_module"

        # Execute
        result = plugin_locator.get_unique_name(mock_module)

        # Verify
        assert result == "test_module"

    def test_get_path(self, plugin_locator):
        """Test get_path method."""
        # Setup
        mock_module = MagicMock(spec=ModuleType)
        mock_module.__file__ = "/path/to/module.py"

        # Execute
        result = plugin_locator.get_path(mock_module)

        # Verify
        assert result == Path("/path/to/module.py")

    def test_get_display_name(self, plugin_locator):
        """Test get_display_name method."""
        # Setup
        mock_module = MagicMock(spec=ModuleType)
        mock_module.__display_name__ = "Display Name"

        # Execute
        result = plugin_locator.get_display_name(mock_module)

        # Verify
        assert result == "Display Name"

    def test_get_description(self, plugin_locator):
        """Test get_description method."""
        # Setup
        mock_module = MagicMock(spec=ModuleType)
        mock_module.__description__ = "Description"

        # Execute
        result = plugin_locator.get_description(mock_module)

        # Verify
        assert result == "Description"

    def test_get_author_exists(self, plugin_locator):
        """Test get_author method when __author__ exists."""
        # Setup
        mock_module = MagicMock(spec=ModuleType)
        mock_module.__author__ = "Author"

        # Execute
        result = plugin_locator.get_author(mock_module)

        # Verify
        assert result == "Author"

    def test_get_author_not_exists(self, plugin_locator):
        """Test get_author method when __author__ doesn't exist."""
        # Setup
        mock_module = MagicMock(spec=ModuleType)
        # No __author__ attribute

        # Execute
        result = plugin_locator.get_author(mock_module)

        # Verify
        assert result is None

    @patch('smib.plugins.locator.inspect.stack')
    def test_get_current_plugin_found(self, mock_stack, plugin_locator):
        """Test get_current_plugin method when the plugin is found."""
        # Setup
        mock_module = MagicMock(spec=ModuleType)
        mock_frame = MagicMock()
        # Create a mock frame info that matches the structure expected by get_current_plugin
        mock_frame_info = MagicMock()
        mock_frame_info.__getitem__.side_effect = lambda idx: mock_frame if idx == 0 else None
        mock_stack.return_value = [mock_frame_info]

        # Mock inspect.getfile
        with patch('smib.plugins.locator.inspect.getfile') as mock_getfile, \
             patch('smib.plugins.locator.Path') as mock_path_class:

            mock_getfile.return_value = "/path/to/plugin/file.py"

            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance

            # Mock get_by_path
            with patch.object(plugin_locator, 'get_by_path') as mock_get_by_path:
                mock_get_by_path.return_value = mock_module

                # Execute
                result = plugin_locator.get_current_plugin()

                # Verify
                assert result == mock_module
                mock_stack.assert_called_once()
                mock_getfile.assert_called_once_with(mock_frame)
                mock_path_instance.resolve.assert_called_once()
                mock_get_by_path.assert_called_once_with(mock_path_instance)

    @patch('smib.plugins.locator.inspect.stack')
    def test_get_current_plugin_not_found(self, mock_stack, plugin_locator):
        """Test get_current_plugin method when the plugin is not found."""
        # Setup
        mock_frame = MagicMock()
        # Create a mock frame info that matches the structure expected by get_current_plugin
        mock_frame_info = MagicMock()
        mock_frame_info.__getitem__.side_effect = lambda idx: mock_frame if idx == 0 else None
        mock_stack.return_value = [mock_frame_info]

        # Mock inspect.getfile
        with patch('smib.plugins.locator.inspect.getfile') as mock_getfile, \
             patch('smib.plugins.locator.Path') as mock_path_class:

            mock_getfile.return_value = "/path/to/plugin/file.py"

            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance

            # Mock get_by_path
            with patch.object(plugin_locator, 'get_by_path') as mock_get_by_path:
                mock_get_by_path.return_value = None

                # Execute
                result = plugin_locator.get_current_plugin()

                # Verify
                assert result is None
                mock_stack.assert_called_once()
                mock_getfile.assert_called_once_with(mock_frame)
                mock_path_instance.resolve.assert_called_once()
                mock_get_by_path.assert_called_once_with(mock_path_instance)

    @patch('smib.plugins.locator.inspect.stack')
    def test_get_current_plugin_value_error(self, mock_stack, plugin_locator):
        """Test get_current_plugin method when ValueError is raised."""
        # Setup
        mock_frame = MagicMock()
        # Create a mock frame info that matches the structure expected by get_current_plugin
        mock_frame_info = MagicMock()
        mock_frame_info.__getitem__.side_effect = lambda idx: mock_frame if idx == 0 else None
        mock_stack.return_value = [mock_frame_info]

        # Mock inspect.getfile
        with patch('smib.plugins.locator.inspect.getfile') as mock_getfile, \
             patch('smib.plugins.locator.Path') as mock_path_class:

            mock_getfile.return_value = "/path/to/plugin/file.py"

            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance

            # Mock get_by_path to raise ValueError
            with patch.object(plugin_locator, 'get_by_path') as mock_get_by_path:
                mock_get_by_path.side_effect = ValueError("Test error")

                # Execute
                result = plugin_locator.get_current_plugin()

                # Verify
                assert result is None
                mock_stack.assert_called_once()
                mock_getfile.assert_called_once_with(mock_frame)
                mock_path_instance.resolve.assert_called_once()
                mock_get_by_path.assert_called_once_with(mock_path_instance)
