import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from http import HTTPMethod

from fastapi import Request, Response
from slack_bolt import BoltResponse
from slack_bolt.request.async_request import AsyncBoltRequest

from smib.events.handlers import BoltRequestMode
from smib.events.handlers.http_event_handler import (
    HttpEventHandler,
    to_async_bolt_request,
    to_http_response,
)
from smib.events.responses.http_bolt_response import HttpBoltResponse


@pytest.mark.asyncio
async def test_http_event_handler_handle():
    """Test HttpEventHandler.handle method."""
    # Create mocks
    mock_bolt_app = AsyncMock()
    mock_bolt_app.async_dispatch = AsyncMock(return_value=BoltResponse(status=200, body="OK"))

    mock_request = MagicMock(spec=Request)
    mock_request.method = "GET"
    mock_request.url = MagicMock()
    mock_request.url.scheme = "https"
    mock_request.url.path = "/test"
    mock_request.url.query = "param=value"
    mock_request.query_params = {"param": "value"}
    mock_request.headers = {"Content-Type": "application/json"}
    mock_request.scope = {"type": "http"}

    mock_context = {"user_id": "U123456"}

    # Create handler
    handler = HttpEventHandler(bolt_app=mock_bolt_app)

    # Call handle method
    with patch("smib.events.handlers.http_event_handler.to_async_bolt_request", new_callable=AsyncMock) as mock_to_bolt_request, \
         patch("smib.events.handlers.http_event_handler.to_http_response", new_callable=AsyncMock) as mock_to_http_response:

        mock_bolt_request = AsyncMock(spec=AsyncBoltRequest)
        mock_to_bolt_request.return_value = mock_bolt_request

        mock_response = (MagicMock(spec=Response), {})
        mock_to_http_response.return_value = mock_response

        result = await handler.handle(mock_request, mock_context)

        # Verify results
        mock_to_bolt_request.assert_called_once_with(mock_request, mock_context)
        mock_bolt_app.async_dispatch.assert_called_once_with(mock_bolt_request)
        mock_to_http_response.assert_called_once_with(mock_bolt_app.async_dispatch.return_value)
        assert result == mock_response


@pytest.mark.asyncio
async def test_to_async_bolt_request():
    """Test to_async_bolt_request function."""
    # Create mocks
    mock_request = MagicMock(spec=Request)
    mock_request.method = "GET"
    mock_request.url = MagicMock()
    mock_request.url.scheme = "https"
    mock_request.url.path = "/test"
    mock_request.url.query = "param=value"
    mock_request.query_params = {"param": "value"}
    mock_request.headers = {"Content-Type": "application/json"}
    mock_request.scope = {"type": "http"}

    mock_context = {"user_id": "U123456"}

    # Call function
    with patch("smib.events.handlers.http_event_handler.jsonable_encoder", return_value={"param": "value"}):
        result = await to_async_bolt_request(mock_request, mock_context)

        # Verify results
        assert isinstance(result, AsyncBoltRequest)
        assert result.body["type"] == "event_callback"
        assert result.body["event"]["type"] == "http"
        assert result.body["event"]["request"]["method"] == HTTPMethod.GET
        assert result.body["event"]["request"]["scheme"] == "https"
        assert result.body["event"]["request"]["path"] == "/test"
        assert result.body["event"]["request"]["query_string"] == "param=value"
        assert result.body["event"]["request"]["query_params"] == {"param": "value"}
        assert result.body["event"]["request"]["scope"] == {"type": "http"}
        assert result.query == {"param": ["value"]}
        assert result.headers == {"content-type": ["application/json"]}
        assert result.mode == BoltRequestMode.HTTP
        assert "user_id" in result.context
        assert result.context["user_id"] == mock_context["user_id"]


@pytest.mark.asyncio
async def test_to_http_response_with_bolt_response():
    """Test to_http_response function with BoltResponse."""
    # Create mock
    mock_bolt_response = MagicMock(spec=BoltResponse)

    # Call function
    with patch("smib.events.handlers.http_event_handler.to_starlette_response", return_value=MagicMock(spec=Response)) as mock_to_starlette:
        result, kwargs = await to_http_response(mock_bolt_response)

        # Verify results
        mock_to_starlette.assert_called_once_with(mock_bolt_response)
        assert result == mock_to_starlette.return_value
        assert kwargs == {}


@pytest.mark.asyncio
async def test_to_http_response_with_http_bolt_response():
    """Test to_http_response function with HttpBoltResponse."""
    # Create mock
    mock_fastapi_response = MagicMock(spec=Response)
    mock_fastapi_kwargs = {"background": MagicMock()}
    mock_http_bolt_response = MagicMock(spec=HttpBoltResponse)
    mock_http_bolt_response.fastapi_response = mock_fastapi_response
    mock_http_bolt_response.fastapi_kwargs = mock_fastapi_kwargs

    # Call function
    result, kwargs = await to_http_response(mock_http_bolt_response)

    # Verify results
    assert result == mock_fastapi_response
    assert kwargs == mock_fastapi_kwargs
