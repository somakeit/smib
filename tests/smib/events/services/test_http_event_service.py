import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from uvicorn import Config, Server

from smib.events.services.http_event_service import HttpEventService
from smib.config import WEBSERVER_HOST, WEBSERVER_PORT, PACKAGE_VERSION, PACKAGE_DISPLAY_NAME, PACKAGE_DESCRIPTION, \
    WEBSERVER_PATH_PREFIX, PACKAGE_NAME, WEBSERVER_FORWARDED_ALLOW_IPS


def test_http_event_service_init():
    """Test HttpEventService initialization."""
    # Create service
    service = HttpEventService()

    # Verify results
    assert service.logger is not None


def test_openapi_tags_lazy_property():
    """Test openapi_tags lazy property."""
    # Create service
    service = HttpEventService()

    # Access property
    tags = service.openapi_tags

    # Verify results
    assert isinstance(tags, list)
    assert len(tags) == 0


def test_fastapi_app_lazy_property():
    """Test fastapi_app lazy property."""
    # Create service
    service = HttpEventService()

    # Access property
    app = service.fastapi_app

    # Verify results
    assert isinstance(app, FastAPI)
    assert app.title == PACKAGE_DISPLAY_NAME
    assert app.version == PACKAGE_VERSION
    assert app.description == PACKAGE_DESCRIPTION
    assert app.root_path == WEBSERVER_PATH_PREFIX


def test_headers_lazy_property():
    """Test headers lazy property."""
    # Create service
    service = HttpEventService()

    # Access property
    headers = service.headers

    # Verify results
    assert isinstance(headers, list)
    assert len(headers) == 3
    assert any(header[0] == "server" for header in headers)
    assert any(header[0] == "x-app-name" and header[1] == PACKAGE_NAME for header in headers)
    assert any(header[0] == "x-app-version" and header[1] == PACKAGE_VERSION for header in headers)


def test_uvicorn_config_lazy_property():
    """Test uvicorn_config lazy property."""
    # Create service
    service = HttpEventService()
    
    # Mock fastapi_app and headers
    service.fastapi_app = MagicMock(spec=FastAPI)
    service.headers = [("test", "value")]

    # Access property
    config = service.uvicorn_config

    # Verify results
    assert isinstance(config, Config)
    assert config.app == service.fastapi_app
    assert config.host == WEBSERVER_HOST
    assert config.port == WEBSERVER_PORT
    assert config.proxy_headers is True
    assert config.forwarded_allow_ips == WEBSERVER_FORWARDED_ALLOW_IPS
    assert config.headers == service.headers


def test_uvicorn_server_lazy_property():
    """Test uvicorn_server lazy property."""
    # Create service
    service = HttpEventService()
    
    # Mock uvicorn_config
    service.uvicorn_config = MagicMock(spec=Config)

    # Access property
    server = service.uvicorn_server

    # Verify results
    assert isinstance(server, Server)
    assert server.config == service.uvicorn_config


@pytest.mark.asyncio
async def test_start():
    """Test start method."""
    # Create service
    service = HttpEventService()
    
    # Mock properties
    service.fastapi_app = MagicMock(spec=FastAPI)
    service.openapi_tags = [{"name": "test"}]
    service.uvicorn_server = MagicMock(spec=Server)
    service.uvicorn_server.serve = AsyncMock()

    # Call method
    await service.start()

    # Verify results
    assert service.fastapi_app.openapi_schema is None
    assert service.fastapi_app.openapi_tags == service.openapi_tags
    service.fastapi_app.setup.assert_called_once()
    service.uvicorn_server.serve.assert_called_once()


@pytest.mark.asyncio
async def test_stop():
    """Test stop method."""
    # Create service
    service = HttpEventService()
    
    # Call method
    await service.stop()
    
    # Currently, this method is empty, so there's nothing to verify
    # This test is included for completeness and to maintain coverage