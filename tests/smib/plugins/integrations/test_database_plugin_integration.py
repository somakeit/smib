import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

from smib.plugins.integrations.database_plugin_integration import DatabasePluginIntegration
from smib.plugins.lifecycle_manager import PluginLifecycleManager


@pytest.fixture
def mock_plugin_lifecycle_manager():
    """Fixture for a mocked PluginLifecycleManager."""
    mock_manager = MagicMock(spec=PluginLifecycleManager)
    mock_manager.plugins = []
    return mock_manager


@pytest.fixture
def database_plugin_integration(mock_plugin_lifecycle_manager):
    """Fixture for a DatabasePluginIntegration instance."""
    return DatabasePluginIntegration(mock_plugin_lifecycle_manager)


class TestDatabasePluginIntegration:
    """Tests for the DatabasePluginIntegration class."""

    def test_init(self, database_plugin_integration, mock_plugin_lifecycle_manager):
        """Test initialization of DatabasePluginIntegration."""
        assert database_plugin_integration.plugin_lifecycle_manager == mock_plugin_lifecycle_manager

    def test_filter_valid_plugins_no_plugins(self, database_plugin_integration):
        """Test filter_valid_plugins when there are no plugins."""
        # Setup
        mock_model = MagicMock()
        mock_model.__module__ = 'test_module'
        sys.modules['test_module'] = MagicMock()
        sys.modules['test_module'].__file__ = '/path/to/model/file.py'

        # Execute
        result = database_plugin_integration.filter_valid_plugins(mock_model)

        # Verify
        assert result is False

    def test_filter_valid_plugins_with_matching_plugin(self, database_plugin_integration):
        """Test filter_valid_plugins when there is a matching plugin."""
        # Setup
        mock_model = MagicMock()
        mock_model.__module__ = 'test_module'
        sys.modules['test_module'] = MagicMock()
        sys.modules['test_module'].__file__ = '/path/to/model/file.py'

        mock_plugin = MagicMock()
        mock_plugin.__file__ = '/path/to/plugin/__init__.py'
        database_plugin_integration.plugin_lifecycle_manager.plugins = [mock_plugin]

        # Mock Path.resolve and is_relative_to
        with patch('smib.plugins.integrations.database_plugin_integration.Path') as mock_path_class:
            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.is_relative_to.return_value = True

            # Execute
            result = database_plugin_integration.filter_valid_plugins(mock_model)

            # Verify
            assert result is True
            mock_path_instance.is_relative_to.assert_called_once()

    def test_filter_valid_plugins_with_non_matching_plugin(self, database_plugin_integration):
        """Test filter_valid_plugins when there is no matching plugin."""
        # Setup
        mock_model = MagicMock()
        mock_model.__module__ = 'test_module'
        sys.modules['test_module'] = MagicMock()
        sys.modules['test_module'].__file__ = '/path/to/model/file.py'

        mock_plugin = MagicMock()
        mock_plugin.__file__ = '/path/to/plugin/__init__.py'
        database_plugin_integration.plugin_lifecycle_manager.plugins = [mock_plugin]

        # Mock Path.resolve and is_relative_to
        with patch('smib.plugins.integrations.database_plugin_integration.Path') as mock_path_class:
            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.is_relative_to.return_value = False

            # Execute
            result = database_plugin_integration.filter_valid_plugins(mock_model)

            # Verify
            assert result is False
            mock_path_instance.is_relative_to.assert_called_once()

    def test_filter_valid_plugins_with_init_file(self, database_plugin_integration):
        """Test filter_valid_plugins when plugin file is __init__.py."""
        # Setup
        mock_model = MagicMock()
        mock_model.__module__ = 'test_module'
        sys.modules['test_module'] = MagicMock()
        sys.modules['test_module'].__file__ = '/path/to/model/file.py'

        mock_plugin = MagicMock()
        mock_plugin.__file__ = '/path/to/plugin/__init__.py'
        database_plugin_integration.plugin_lifecycle_manager.plugins = [mock_plugin]

        # Mock Path and its methods
        with patch('smib.plugins.integrations.database_plugin_integration.Path') as mock_path_class:
            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.name = "__init__.py"
            mock_path_instance.parent = MagicMock(spec=Path)
            mock_path_instance.is_relative_to.return_value = True

            # Execute
            result = database_plugin_integration.filter_valid_plugins(mock_model)

            # Verify
            assert result is True
            mock_path_instance.is_relative_to.assert_called_once()