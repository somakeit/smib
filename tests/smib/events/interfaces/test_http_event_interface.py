import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from fastapi import Request, Response
from fastapi.routing import APIRouter
from slack_bolt.app.async_app import AsyncApp
from starlette.routing import Match, BaseRoute

from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.interfaces.http_event_interface import (
    HttpEventInterface,
    preserve_http_response,
    generate_route_matcher,
    extract_request_parameter_value,
    clean_signature,
    get_reserved_parameter_names,
)
from smib.events.responses.http_bolt_response import HttpBoltResponse
from smib.events.services.http_event_service import HttpEventService

from inspect import Signature, Parameter


def test_http_event_interface_init():
    """Test HttpEventInterface initialization."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=HttpEventHandler)
    mock_service = MagicMock(spec=HttpEventService)

    # Create interface
    interface = HttpEventInterface(bolt_app=mock_bolt_app, handler=mock_handler, service=mock_service)

    # Verify results
    assert interface.bolt_app == mock_bolt_app
    assert interface.handler == mock_handler
    assert interface.service == mock_service
    assert isinstance(interface.routers, dict)
    assert isinstance(interface.current_router, APIRouter)


def test_add_openapi_tags():
    """Test add_openapi_tags method."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=HttpEventHandler)
    mock_service = MagicMock(spec=HttpEventService)
    mock_service.openapi_tags = []

    # Create interface
    interface = HttpEventInterface(bolt_app=mock_bolt_app, handler=mock_handler, service=mock_service)

    # Call method
    tags = [{"name": "test", "description": "Test tag"}]
    interface.add_openapi_tags(tags)

    # Verify results
    assert mock_service.openapi_tags == tags


@pytest.mark.asyncio
@patch("smib.events.interfaces.http_event_interface.clean_signature")
@patch("smib.events.interfaces.http_event_interface.extract_request_parameter_value")
@patch("smib.events.interfaces.http_event_interface.generate_route_matcher")
@patch("smib.events.interfaces.http_event_interface.preserve_http_response")
@patch("smib.events.interfaces.http_event_interface.makefun.with_signature")
async def test_route_decorator(
    mock_with_signature,
    mock_preserve_http_response,
    mock_generate_route_matcher,
    mock_extract_request_parameter_value,
    mock_clean_signature,
):
    """Test __route_decorator method."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=HttpEventHandler)
    mock_service = MagicMock(spec=HttpEventService)

    # Create interface
    interface = HttpEventInterface(bolt_app=mock_bolt_app, handler=mock_handler, service=mock_service)

    # Mock the current_router
    interface.current_router = MagicMock(spec=APIRouter)
    interface.current_router.routes = []

    # Create a test function
    async def test_func(request: Request, param: str):
        return Response(content="Test")

    # Mock the signature
    mock_signature = MagicMock(spec=Signature)
    mock_clean_signature.return_value = mock_signature

    # Mock the wrapper function
    mock_wrapper = AsyncMock()
    mock_with_signature.return_value = lambda f: mock_wrapper

    # Mock the route
    mock_route = MagicMock(spec=BaseRoute)
    interface.current_router.routes.append(mock_route)

    # Mock the matcher
    mock_matcher = AsyncMock()
    mock_generate_route_matcher.return_value = mock_matcher

    # Mock the response_preserving_func
    mock_response_preserving_func = AsyncMock()
    mock_preserve_http_response.return_value = mock_response_preserving_func

    # Call the decorator
    decorator = interface._HttpEventInterface__route_decorator("/test", ["GET"])
    result = decorator(test_func)

    # Verify results
    assert result == test_func
    mock_clean_signature.assert_called_once_with(Signature.from_callable(test_func))
    mock_with_signature.assert_called_once()
    interface.current_router.add_api_route.assert_called_once_with("/test", mock_wrapper, methods=["GET"])
    mock_generate_route_matcher.assert_called_once_with(mock_route)
    mock_preserve_http_response.assert_called_once_with(test_func)
    mock_bolt_app.event.assert_called_once_with('http', matchers=[mock_matcher])
    mock_bolt_app.event.return_value.assert_called_once_with(mock_response_preserving_func)


def test_http_methods():
    """Test HTTP method decorators."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=HttpEventHandler)
    mock_service = MagicMock(spec=HttpEventService)

    # Create interface
    interface = HttpEventInterface(bolt_app=mock_bolt_app, handler=mock_handler, service=mock_service)

    # Mock the __route_decorator method
    interface._HttpEventInterface__route_decorator = MagicMock()
    mock_decorator = MagicMock()
    interface._HttpEventInterface__route_decorator.return_value = mock_decorator

    # Test GET method
    result = interface.get("/test", response_model=dict)
    interface._HttpEventInterface__route_decorator.assert_called_once_with("/test", ["GET"], response_model=dict)
    assert result == mock_decorator

    # Reset mock
    interface._HttpEventInterface__route_decorator.reset_mock()

    # Test PUT method
    result = interface.put("/test", response_model=dict)
    interface._HttpEventInterface__route_decorator.assert_called_once_with("/test", ["PUT"], response_model=dict)
    assert result == mock_decorator

    # Reset mock
    interface._HttpEventInterface__route_decorator.reset_mock()

    # Test POST method
    result = interface.post("/test", response_model=dict)
    interface._HttpEventInterface__route_decorator.assert_called_once_with("/test", ["POST"], response_model=dict)
    assert result == mock_decorator

    # Reset mock
    interface._HttpEventInterface__route_decorator.reset_mock()

    # Test DELETE method
    result = interface.delete("/test", response_model=dict)
    interface._HttpEventInterface__route_decorator.assert_called_once_with("/test", ["DELETE"], response_model=dict)
    assert result == mock_decorator

    # Reset mock
    interface._HttpEventInterface__route_decorator.reset_mock()

    # Test PATCH method
    result = interface.patch("/test", response_model=dict)
    interface._HttpEventInterface__route_decorator.assert_called_once_with("/test", ["PATCH"], response_model=dict)
    assert result == mock_decorator


@pytest.mark.asyncio
async def test_preserve_http_response():
    """Test preserve_http_response function."""
    # Create a test function
    async def test_func(*args, **kwargs):
        return Response(content="Test")

    # Wrap the function
    wrapped_func = preserve_http_response(test_func)

    # Call the wrapped function
    result = await wrapped_func("arg1", key="value")

    # Verify results
    assert isinstance(result, HttpBoltResponse)
    assert result.status == 0
    assert result.body == ''
    assert isinstance(result.fastapi_response, Response)
    assert result.fastapi_kwargs == {"key": "value"}


@pytest.mark.asyncio
async def test_generate_route_matcher():
    """Test generate_route_matcher function."""
    # Create mock route
    mock_route = MagicMock(spec=BaseRoute)
    mock_route.matches.return_value = (Match.FULL.value, {})

    # Create matcher
    matcher = generate_route_matcher(mock_route)

    # Call matcher
    event = {"request": {"scope": {"type": "http"}}}
    result = await matcher(event)

    # Verify results
    assert result is True
    mock_route.matches.assert_called_once_with(event["request"]["scope"])

    # Test with non-matching route
    mock_route.matches.return_value = (Match.NONE.value, {})
    result = await matcher(event)
    assert result is False


def test_extract_request_parameter_value():
    """Test extract_request_parameter_value function."""
    # Create a signature with a Request parameter
    params = [
        Parameter(name="request", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=Request),
        Parameter(name="param", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
    ]
    signature = Signature(parameters=params)

    # Create args and kwargs
    mock_request = MagicMock(spec=Request)
    args = [mock_request, "value"]
    kwargs = {}

    # Call function
    result = extract_request_parameter_value(signature, args, kwargs)

    # Verify results
    assert result == mock_request

    # Test with kwargs
    args = []
    kwargs = {"request": mock_request, "param": "value"}
    result = extract_request_parameter_value(signature, args, kwargs)
    assert result == mock_request

    # Test with no Request parameter
    params = [
        Parameter(name="param1", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
        Parameter(name="param2", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=int),
    ]
    signature = Signature(parameters=params)
    args = ["value", 123]
    kwargs = {}
    result = extract_request_parameter_value(signature, args, kwargs)
    assert result is None


def test_clean_signature():
    """Test clean_signature function."""
    # Create a signature with reserved parameters
    params = [
        Parameter(name="say", kind=Parameter.POSITIONAL_OR_KEYWORD),
        Parameter(name="context", kind=Parameter.POSITIONAL_OR_KEYWORD),
        Parameter(name="param", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
    ]
    signature = Signature(parameters=params)

    # Mock get_reserved_parameter_names
    with patch("smib.events.interfaces.http_event_interface.get_reserved_parameter_names", return_value={"say", "context"}):
        # Call function
        result = clean_signature(signature)

        # Verify results
        assert "say" not in result.parameters
        assert "context" not in result.parameters
        assert "param" in result.parameters
        assert "_http_request_" in result.parameters
        assert result.parameters["_http_request_"].annotation == Request

    # Test with existing Request parameter
    params = [
        Parameter(name="request", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=Request),
        Parameter(name="param", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
    ]
    signature = Signature(parameters=params)

    with patch("smib.events.interfaces.http_event_interface.get_reserved_parameter_names", return_value=set()):
        # Call function
        result = clean_signature(signature)

        # Verify results
        assert "request" in result.parameters
        assert "param" in result.parameters
        assert "_http_request_" not in result.parameters


def test_get_reserved_parameter_names():
    """Test get_reserved_parameter_names function."""
    # Call function
    with patch("smib.events.interfaces.http_event_interface.AsyncArgs") as mock_async_args:
        mock_async_args.__annotations__ = {"say": callable, "context": dict}
        result = get_reserved_parameter_names()

        # Verify results
        assert result == {"say", "context"}


@pytest.mark.asyncio
async def test_route_decorator_wrapper():
    """Test the wrapper function inside __route_decorator."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=HttpEventHandler)
    mock_service = MagicMock(spec=HttpEventService)

    # Mock handler.handle to return a response and kwargs
    mock_response = MagicMock(spec=Response)
    mock_response_kwargs = {"background": MagicMock()}
    mock_handler.handle = AsyncMock(return_value=(mock_response, mock_response_kwargs))

    # Create interface
    interface = HttpEventInterface(bolt_app=mock_bolt_app, handler=mock_handler, service=mock_service)

    # Mock the current_router
    interface.current_router = MagicMock(spec=APIRouter)
    interface.current_router.routes = []
    mock_route = MagicMock(spec=BaseRoute)
    interface.current_router.routes.append(mock_route)

    # Create a test function
    async def test_func(request: Request, param: str):
        return Response(content="Test")

    # Apply the decorator
    decorator = interface._HttpEventInterface__route_decorator("/test", ["GET"])
    decorated_func = decorator(test_func)

    # Extract the wrapper function from add_api_route
    wrapper_func = interface.current_router.add_api_route.call_args[0][1]

    # Create a mock request
    mock_request = MagicMock(spec=Request)

    # Call the wrapper function
    result = await wrapper_func(mock_request, "test_param")

    # Verify results
    mock_handler.handle.assert_called_once()
    assert mock_handler.handle.call_args[0][0] == mock_request  # First arg should be request
    assert "test_param" in mock_handler.handle.call_args[0][1].values()  # Second arg should contain param
    assert result == mock_response  # Result should be the response from handler.handle
