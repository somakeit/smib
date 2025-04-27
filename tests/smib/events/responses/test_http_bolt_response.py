import pytest
from unittest.mock import MagicMock

from slack_bolt import BoltResponse
from fastapi import Response

from smib.events.responses.http_bolt_response import HttpBoltResponse


def test_http_bolt_response_init():
    """Test HttpBoltResponse initialization."""
    # Test with minimal parameters
    response = HttpBoltResponse(status=200)
    assert response.status == 200
    assert response.body == ""
    assert "content-type" in response.headers
    assert response.fastapi_response is None
    assert response.fastapi_kwargs is None

    # Test with all parameters
    mock_fastapi_response = MagicMock(spec=Response)
    mock_fastapi_kwargs = {"background": MagicMock()}

    response = HttpBoltResponse(
        status=404,
        body={"error": "Not Found"},
        headers={"Content-Type": "application/json"},
        fastapi_response=mock_fastapi_response,
        fastapi_kwargs=mock_fastapi_kwargs
    )

    assert response.status == 404
    assert response.body == '{"error": "Not Found"}'
    assert "content-type" in response.headers
    assert response.headers["content-type"] == ["application/json"]
    assert response.fastapi_response == mock_fastapi_response
    assert response.fastapi_kwargs == mock_fastapi_kwargs


def test_http_bolt_response_repr():
    """Test HttpBoltResponse __repr__ method."""
    # Create a response with all parameters
    mock_fastapi_response = MagicMock(spec=Response)
    mock_fastapi_kwargs = {"background": MagicMock()}

    response = HttpBoltResponse(
        status=404,
        body={"error": "Not Found"},
        headers={"Content-Type": "application/json"},
        fastapi_response=mock_fastapi_response,
        fastapi_kwargs=mock_fastapi_kwargs
    )

    # Get the string representation
    repr_str = repr(response)

    # Verify it contains the custom fields
    assert "fastapi_response=" in repr_str
    assert "fastapi_kwargs=" in repr_str


def test_http_bolt_response_inheritance():
    """Test HttpBoltResponse inherits from BoltResponse."""
    response = HttpBoltResponse(status=200)
    assert isinstance(response, BoltResponse)

    # Test that it inherits BoltResponse's behavior
    bolt_response = BoltResponse(status=200, body="OK", headers={"X-Test": "test"})
    http_bolt_response = HttpBoltResponse(status=200, body="OK", headers={"X-Test": "test"})

    assert http_bolt_response.status == bolt_response.status
    assert http_bolt_response.body == bolt_response.body
    assert http_bolt_response.headers == bolt_response.headers
