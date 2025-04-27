import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.middleware.async_custom_middleware import AsyncCustomMiddleware
from smib.plugins.integrations.slack_plugin_integration import SlackPluginIntegration


@pytest.fixture
def mock_bolt_app():
    """Fixture for a mocked AsyncApp."""
    mock_app = MagicMock(spec=AsyncApp)
    mock_app._async_listeners = []
    mock_app._async_middleware_list = []
    return mock_app


@pytest.fixture
def slack_plugin_integration(mock_bolt_app):
    """Fixture for a SlackPluginIntegration instance."""
    return SlackPluginIntegration(mock_bolt_app)


class TestSlackPluginIntegration:
    """Tests for the SlackPluginIntegration class."""

    def test_init(self, slack_plugin_integration, mock_bolt_app):
        """Test initialization of SlackPluginIntegration."""
        assert slack_plugin_integration.bolt_app == mock_bolt_app
        assert isinstance(slack_plugin_integration.logger, object)

    def test_disconnect_plugin(self, slack_plugin_integration):
        """Test disconnect_plugin calls both disconnect_listeners and disconnect_middlewares."""
        # Setup
        mock_plugin = MagicMock()

        # Mock the disconnect methods
        with patch.object(slack_plugin_integration, 'disconnect_listeners') as mock_disconnect_listeners, \
             patch.object(slack_plugin_integration, 'disconnect_middlewares') as mock_disconnect_middlewares:

            # Execute
            slack_plugin_integration.disconnect_plugin(mock_plugin)

            # Verify
            mock_disconnect_listeners.assert_called_once_with(mock_plugin)
            mock_disconnect_middlewares.assert_called_once_with(mock_plugin)

    def test_disconnect_listeners_no_listeners(self, slack_plugin_integration):
        """Test disconnect_listeners when there are no listeners."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        slack_plugin_integration.bolt_app._async_listeners = []

        # Execute
        slack_plugin_integration.disconnect_listeners(mock_plugin)

        # Verify - no exception should be raised

    def test_disconnect_listeners_with_listeners(self, slack_plugin_integration):
        """Test disconnect_listeners when there are listeners to remove."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        # Create a mock listener
        mock_listener = MagicMock()
        mock_listener.ack_function.__module__ = "test_module"
        mock_listener.ack_function.__name__ = "test_listener"
        sys.modules["test_module"] = MagicMock()
        sys.modules["test_module"].__file__ = "/path/to/plugin/listener.py"

        slack_plugin_integration.bolt_app._async_listeners = [mock_listener]

        # Mock Path.resolve and is_relative_to
        with patch('smib.plugins.integrations.slack_plugin_integration.Path') as mock_path_class:
            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.is_relative_to.return_value = True
            mock_path_instance.name = "__init__.py"
            mock_path_instance.parent = MagicMock(spec=Path)

            # Execute
            slack_plugin_integration.disconnect_listeners(mock_plugin)

            # Verify
            assert len(slack_plugin_integration.bolt_app._async_listeners) == 0

    def test_disconnect_listeners_with_non_matching_listeners(self, slack_plugin_integration):
        """Test disconnect_listeners when there are listeners but none match the plugin."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        # Create a mock listener
        mock_listener = MagicMock()
        mock_listener.ack_function.__module__ = "test_module"
        mock_listener.ack_function.__name__ = "test_listener"
        sys.modules["test_module"] = MagicMock()
        sys.modules["test_module"].__file__ = "/path/to/other/listener.py"

        slack_plugin_integration.bolt_app._async_listeners = [mock_listener]

        # Mock Path.resolve and is_relative_to
        with patch('smib.plugins.integrations.slack_plugin_integration.Path') as mock_path_class:
            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.is_relative_to.return_value = False
            mock_path_instance.name = "__init__.py"
            mock_path_instance.parent = MagicMock(spec=Path)

            # Execute
            slack_plugin_integration.disconnect_listeners(mock_plugin)

            # Verify
            assert len(slack_plugin_integration.bolt_app._async_listeners) == 1

    def test_disconnect_middlewares_no_middlewares(self, slack_plugin_integration):
        """Test disconnect_middlewares when there are no middlewares."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        slack_plugin_integration.bolt_app._async_middleware_list = []

        # Execute
        slack_plugin_integration.disconnect_middlewares(mock_plugin)

        # Verify - no exception should be raised

    def test_disconnect_middlewares_with_middlewares(self, slack_plugin_integration):
        """Test disconnect_middlewares when there are middlewares to remove."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        # Create a mock middleware
        mock_middleware = MagicMock(spec=AsyncCustomMiddleware)
        mock_middleware.func = MagicMock()
        mock_middleware.func.__module__ = "test_module"
        mock_middleware.func.__name__ = "test_middleware"
        sys.modules["test_module"] = MagicMock()
        sys.modules["test_module"].__file__ = "/path/to/plugin/middleware.py"

        slack_plugin_integration.bolt_app._async_middleware_list = [mock_middleware]

        # Mock Path.resolve and is_relative_to
        with patch('smib.plugins.integrations.slack_plugin_integration.Path') as mock_path_class:
            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.is_relative_to.return_value = True
            mock_path_instance.name = "__init__.py"
            mock_path_instance.parent = MagicMock(spec=Path)

            # Execute
            slack_plugin_integration.disconnect_middlewares(mock_plugin)

            # Verify
            assert len(slack_plugin_integration.bolt_app._async_middleware_list) == 0

    def test_disconnect_middlewares_with_non_matching_middlewares(self, slack_plugin_integration):
        """Test disconnect_middlewares when there are middlewares but none match the plugin."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        # Create a mock middleware
        mock_middleware = MagicMock(spec=AsyncCustomMiddleware)
        mock_middleware.func = MagicMock()
        mock_middleware.func.__module__ = "test_module"
        mock_middleware.func.__name__ = "test_middleware"
        sys.modules["test_module"] = MagicMock()
        sys.modules["test_module"].__file__ = "/path/to/other/middleware.py"

        slack_plugin_integration.bolt_app._async_middleware_list = [mock_middleware]

        # Mock Path.resolve and is_relative_to
        with patch('smib.plugins.integrations.slack_plugin_integration.Path') as mock_path_class:
            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.is_relative_to.return_value = False
            mock_path_instance.name = "__init__.py"
            mock_path_instance.parent = MagicMock(spec=Path)

            # Execute
            slack_plugin_integration.disconnect_middlewares(mock_plugin)

            # Verify
            assert len(slack_plugin_integration.bolt_app._async_middleware_list) == 1

    def test_disconnect_middlewares_with_non_custom_middleware(self, slack_plugin_integration):
        """Test disconnect_middlewares when there are middlewares but they are not AsyncCustomMiddleware."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        # Create a mock middleware that is not AsyncCustomMiddleware
        mock_middleware = MagicMock()  # Not spec=AsyncCustomMiddleware

        slack_plugin_integration.bolt_app._async_middleware_list = [mock_middleware]

        # Execute
        slack_plugin_integration.disconnect_middlewares(mock_plugin)

        # Verify
        assert len(slack_plugin_integration.bolt_app._async_middleware_list) == 1
