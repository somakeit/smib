import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

from fastapi import APIRouter
from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.plugins.integrations.http_plugin_integration import HttpPluginIntegration
from smib.plugins.locator import PluginLocator


@pytest.fixture
def mock_http_event_interface():
    """Fixture for a mocked HttpEventInterface."""
    mock_interface = MagicMock(spec=HttpEventInterface)
    mock_interface.service = MagicMock()
    mock_interface.service.fastapi_app = MagicMock()
    mock_interface.routers = {}
    return mock_interface


@pytest.fixture
def mock_plugin_locator():
    """Fixture for a mocked PluginLocator."""
    return MagicMock(spec=PluginLocator)


@pytest.fixture
def http_plugin_integration(mock_http_event_interface, mock_plugin_locator):
    """Fixture for a HttpPluginIntegration instance."""
    return HttpPluginIntegration(mock_http_event_interface, mock_plugin_locator)


class TestHttpPluginIntegration:
    """Tests for the HttpPluginIntegration class."""

    def test_init(self, http_plugin_integration, mock_http_event_interface, mock_plugin_locator):
        """Test initialization of HttpPluginIntegration."""
        assert http_plugin_integration.http_event_interface == mock_http_event_interface
        assert http_plugin_integration.plugin_locator == mock_plugin_locator
        assert http_plugin_integration.fastapi_app == mock_http_event_interface.service.fastapi_app
        assert isinstance(http_plugin_integration.logger, object)
        assert http_plugin_integration.tag_metadata == []

    def test_disconnect_plugin_no_routes(self, http_plugin_integration):
        """Test disconnect_plugin when there are no routes."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        http_plugin_integration.http_event_interface.routers = {}
        http_plugin_integration.fastapi_app.routes = []

        # Execute
        http_plugin_integration.disconnect_plugin(mock_plugin)

        # Verify - no exception should be raised

    def test_disconnect_plugin_with_routes(self, http_plugin_integration):
        """Test disconnect_plugin when there are routes to remove."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        # Create a mock route
        mock_route = MagicMock()
        mock_route.endpoint.__module__ = "test_module"
        sys.modules["test_module"] = MagicMock()
        sys.modules["test_module"].__file__ = "/path/to/plugin/route.py"

        # Add the route to the fastapi_app
        http_plugin_integration.fastapi_app.routes = [mock_route]

        # Create a mock router with routes
        mock_router = MagicMock()
        mock_router.routes = [mock_route]
        http_plugin_integration.http_event_interface.routers = {"test_router": mock_router}

        # Mock Path.resolve and is_relative_to
        with patch('smib.plugins.integrations.http_plugin_integration.Path') as mock_path_class:
            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.is_relative_to.return_value = True
            mock_path_instance.name = "__init__.py"
            mock_path_instance.parent = MagicMock(spec=Path)

            # Execute
            http_plugin_integration.disconnect_plugin(mock_plugin)

            # Verify
            assert len(http_plugin_integration.fastapi_app.routes) == 0
            assert len(mock_router.routes) == 0

    def test_initialise_plugin_router(self, http_plugin_integration, mock_plugin_locator):
        """Test initialise_plugin_router."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin_locator.get_unique_name.return_value = "test_unique_name"
        mock_plugin_locator.get_display_name.return_value = "Test Display Name"
        mock_plugin_locator.get_description.return_value = "Test description"

        # Mock APIRouter
        with patch('smib.plugins.integrations.http_plugin_integration.APIRouter') as mock_api_router:
            mock_router = MagicMock(spec=APIRouter)
            mock_api_router.return_value = mock_router

            # Execute
            http_plugin_integration.initialise_plugin_router(mock_plugin)

            # Verify
            assert len(http_plugin_integration.tag_metadata) == 1
            assert http_plugin_integration.tag_metadata[0]["name"] == "Test Display Name"
            assert http_plugin_integration.tag_metadata[0]["description"] == "Test description"
            assert http_plugin_integration.http_event_interface.current_router == mock_router
            assert http_plugin_integration.http_event_interface.routers["test_unique_name"] == mock_router
            mock_api_router.assert_called_once_with(tags=["Test Display Name"])

    def test_finalise_http_setup(self, http_plugin_integration):
        """Test finalise_http_setup."""
        # Setup
        http_plugin_integration.tag_metadata = [{"name": "Test", "description": "Test"}]

        mock_router1 = MagicMock(spec=APIRouter)
        mock_router2 = MagicMock(spec=APIRouter)
        http_plugin_integration.http_event_interface.routers = {
            "router1": mock_router1,
            "router2": mock_router2
        }

        # Create a mock for openapi_tags
        mock_openapi_tags = MagicMock()
        http_plugin_integration.http_event_interface.service.openapi_tags = mock_openapi_tags

        # Execute
        http_plugin_integration.finalise_http_setup()

        # Verify
        # Check that += was called on openapi_tags with tag_metadata
        mock_openapi_tags.__iadd__.assert_called_once_with(http_plugin_integration.tag_metadata)
        http_plugin_integration.fastapi_app.include_router.assert_any_call(mock_router1)
        http_plugin_integration.fastapi_app.include_router.assert_any_call(mock_router2)
        assert http_plugin_integration.fastapi_app.include_router.call_count == 2
