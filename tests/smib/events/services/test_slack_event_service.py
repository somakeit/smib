import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from aiohttp import WSMessage
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from smib.events.services.slack_event_service import SlackEventService
from smib.config import SLACK_APP_TOKEN


def test_slack_event_service_init():
    """Test SlackEventService initialization."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)

    # Create service
    service = SlackEventService(bolt_app=mock_bolt_app)

    # Verify results
    assert service.bolt_app == mock_bolt_app
    assert service.logger is not None


@patch("smib.events.services.slack_event_service.AsyncSocketModeHandler")
def test_service_lazy_property(mock_async_socket_mode_handler):
    """Test service lazy property."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=AsyncSocketModeHandler)
    mock_client = MagicMock()
    mock_client.on_message_listeners = []
    mock_handler.client = mock_client
    mock_async_socket_mode_handler.return_value = mock_handler

    # Create service
    service = SlackEventService(bolt_app=mock_bolt_app)

    # Mock log_number_of_connections
    service.log_number_of_connections = MagicMock()

    # Access property
    result = service.service

    # Verify results
    assert result == mock_handler
    mock_async_socket_mode_handler.assert_called_once_with(mock_bolt_app, app_token=SLACK_APP_TOKEN)
    assert service.log_number_of_connections in mock_handler.client.on_message_listeners


@pytest.mark.asyncio
async def test_log_number_of_connections():
    """Test log_number_of_connections method."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_message = MagicMock(spec=WSMessage)

    # Create hello message
    hello_message = {
        "type": "hello",
        "num_connections": 5
    }
    mock_message.data = json.dumps(hello_message)

    # Create service
    service = SlackEventService(bolt_app=mock_bolt_app)
    service.logger = MagicMock()

    # Call method
    await service.log_number_of_connections(mock_message)

    # Verify results
    service.logger.info.assert_called_once_with("Number of active slack websocket connections: 5")

    # Test with non-hello message
    other_message = {
        "type": "other",
        "data": "test"
    }
    mock_message.data = json.dumps(other_message)

    # Reset mock
    service.logger.reset_mock()

    # Call method
    await service.log_number_of_connections(mock_message)

    # Verify results
    service.logger.info.assert_not_called()


@pytest.mark.asyncio
async def test_start():
    """Test start method."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)

    # Create service
    service = SlackEventService(bolt_app=mock_bolt_app)

    # Mock service property
    service.service = MagicMock(spec=AsyncSocketModeHandler)
    service.service.start_async = AsyncMock()

    # Call method
    await service.start()

    # Verify results
    service.service.start_async.assert_called_once()


@pytest.mark.asyncio
async def test_stop():
    """Test stop method."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)

    # Create service
    service = SlackEventService(bolt_app=mock_bolt_app)

    # Mock service property
    service.service = MagicMock(spec=AsyncSocketModeHandler)
    service.service.close_async = AsyncMock()

    # Call method
    await service.stop()

    # Verify results
    service.service.close_async.assert_called_once()
