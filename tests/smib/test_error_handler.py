import pytest
import pprint
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from slack_bolt.error import BoltUnhandledRequestError
from slack_bolt.request.async_request import AsyncBoltRequest

from smib.error_handler import slack_bolt_error_handler, default_error_handler
from smib.events.handlers import BoltRequestMode
from smib.events.responses.http_bolt_response import HttpBoltResponse


@pytest.mark.asyncio
@patch("smib.error_handler.http_exception_handler", new_callable=AsyncMock)
@patch("smib.error_handler.default_error_handler.handle", new_callable=AsyncMock)
async def test_socket_mode_with_unhandled_request_error(mock_handle, mock_http_handler):
    """
    Test Socket Mode with BoltUnhandledRequestError.
    """
    # Mock inputs
    mock_request = AsyncMock()
    mock_request.mode = BoltRequestMode.SOCKET_MODE

    mock_response = MagicMock()
    mock_error = BoltUnhandledRequestError(request=mock_request, current_response=mock_response)

    # Call the handler
    result = await slack_bolt_error_handler(
        error=mock_error,
        request=mock_request,
        body={},
        response=mock_response,
        logger=MagicMock()
    )

    # Assertions
    mock_handle.assert_called_once_with(mock_error, mock_request, mock_response)
    assert result == mock_handle.return_value
    mock_http_handler.assert_not_called()  # Ensure HTTP handler is not called


@pytest.mark.asyncio
@patch("smib.error_handler.http_exception_handler", new_callable=AsyncMock)
async def test_http_mode_with_http_exception(mock_http_handler):
    """
    Test HTTP Mode with HTTPException.
    """
    # Mock inputs
    mock_request = AsyncMock()
    mock_request.mode = BoltRequestMode.HTTP

    mock_response = MagicMock()
    mock_error = HTTPException(status_code=404, detail="Not Found")

    mock_logger = MagicMock()

    # Mock FastAPI http_exception_handler response
    mock_http_handler.return_value = MagicMock(
        status_code=404,
        body="Not Found",
        headers={"content-type": "application/json"}  # Fix: Use lowercase
    )

    # Call the handler
    result = await slack_bolt_error_handler(
        error=mock_error,
        request=mock_request,
        body={},
        response=mock_response,
        logger=mock_logger
    )

    # Assertions
    mock_http_handler.assert_called_once_with(None, mock_error)
    assert isinstance(result, HttpBoltResponse)
    assert result.status == 404
    assert result.body == "Not Found"
    print(result.headers)
    assert result.headers == {"content-type": ["application/json"]}  # Fix: Match lowercase headers



@pytest.mark.asyncio
async def test_fallback_case_logs_error():
    """
    Test the fallback case where none of the specific cases are matched.
    """
    # Mock inputs
    mock_request = AsyncMock()
    mock_request.mode = "UNKNOWN_MODE"  # Unknown mode for fallback

    mock_response = MagicMock()
    mock_error = Exception("Generic error message")
    mock_logger = MagicMock()

    mock_body = {"key": "value"}

    # Call the handler
    result = await slack_bolt_error_handler(
        error=mock_error,
        request=mock_request,
        body=mock_body,
        response=mock_response,
        logger=mock_logger
    )

    # Assertions
    mock_logger.info.assert_called_once_with(f"Request mode: {mock_request.mode}")
    mock_logger.warning.assert_called_once_with(
        pprint.pformat(mock_body, sort_dicts=False),
        exc_info=mock_error
    )
    assert result is None