import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from smib.events.services.http_event_service import HttpEventService
from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from smib.db.manager import DatabaseManager


@pytest.fixture
def mock_bolt_app():
    """Mock Slack Bolt app to avoid needing Slack credentials."""
    return MagicMock()


@pytest.fixture
def mock_database():
    """Mock database manager to avoid needing a real MongoDB connection."""
    db = AsyncMock(spec=DatabaseManager)
    db.get_db_version = AsyncMock(return_value="7.0.0")
    return db


@pytest.fixture
def http_service():
    """Create HTTP event service with FastAPI app."""
    return HttpEventService()


@pytest.fixture
def api_interface(mock_bolt_app, http_service):
    """Create API event interface for registering routes."""
    http_handler = HttpEventHandler(mock_bolt_app)
    return ApiEventInterface(mock_bolt_app, http_handler, http_service)


@pytest.fixture
def register_core_plugin(api_interface, mock_database):
    """Register the core plugin endpoints (including /api/version)."""
    from plugins.core.core import register
    register(api_interface, mock_database)


@pytest.mark.asyncio
async def test_api_version_returns_200(http_service, register_core_plugin):
    """
    Test that /api/version endpoint returns 200 status code.
    
    According to OpenAPI spec:
    - Path: /api/version
    - Method: GET
    - Expected Status: 200
    """
    app = http_service.fastapi_app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        response = await client.get("/api/version")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_version_returns_correct_schema(http_service, register_core_plugin, mock_database):
    """
    Test that /api/version endpoint returns data matching the Versions schema.
    
    According to OpenAPI spec, the response should have:
    - smib: string (SMIB version)
    - mongo: string (MongoDB version)
    """
    app = http_service.fastapi_app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        response = await client.get("/api/version")
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Check required fields exist
    assert "smib" in data, "Response should contain 'smib' field"
    assert "mongo" in data, "Response should contain 'mongo' field"
    
    # Check field types
    assert isinstance(data["smib"], str), "'smib' should be a string"
    assert isinstance(data["mongo"], str), "'mongo' should be a string"
    
    # Verify MongoDB version from mock
    assert data["mongo"] == "7.0.0"


@pytest.mark.asyncio
async def test_api_version_content_type_is_json(http_service, register_core_plugin):
    """
    Test that /api/version endpoint returns application/json content type.
    
    According to OpenAPI spec, response content type should be:
    - application/json
    """
    app = http_service.fastapi_app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        response = await client.get("/api/version")
    
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_api_version_is_tagged_as_core(http_service, register_core_plugin):
    """
    Test that /api/version endpoint is tagged with 'Core' in OpenAPI schema.
    """
    app = http_service.fastapi_app
    openapi_schema = app.openapi()
    
    # Check that the endpoint exists in the schema
    assert "/api/version" in openapi_schema["paths"]
    
    # Check that it has the GET method
    assert "get" in openapi_schema["paths"]["/api/version"]
    
    # Check that it's tagged as "Core"
    endpoint = openapi_schema["paths"]["/api/version"]["get"]
    assert "tags" in endpoint
    assert "Core" in endpoint["tags"]


@pytest.mark.asyncio
async def test_api_version_operation_id(http_service, register_core_plugin):
    """
    Test that /api/version has the correct operation ID.
    
    According to OpenAPI spec:
    - operationId: get_version_api_version_get
    """
    app = http_service.fastapi_app
    openapi_schema = app.openapi()
    
    endpoint = openapi_schema["paths"]["/api/version"]["get"]
    assert endpoint["operationId"] == "get_version_api_version_get"


@pytest.mark.asyncio
async def test_api_version_smib_version_format(http_service, register_core_plugin):
    """
    Test that the smib version follows semantic versioning format.
    
    According to OpenAPI spec example: "2.0.0"
    """
    app = http_service.fastapi_app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        response = await client.get("/api/version")
    
    assert response.status_code == 200
    data = response.json()
    
    # Version should be non-empty string
    assert len(data["smib"]) > 0, "SMIB version should not be empty"
    
    # Should contain at least one digit (basic version check)
    assert any(char.isdigit() for char in data["smib"]), "Version should contain digits"


@pytest.mark.asyncio
async def test_api_version_no_extra_fields(http_service, register_core_plugin):
    """
    Test that /api/version response contains only expected fields.
    
    According to schema, only 'smib' and 'mongo' should be present.
    """
    app = http_service.fastapi_app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        response = await client.get("/api/version")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that only expected fields are present
    expected_fields = {"smib", "mongo"}
    actual_fields = set(data.keys())
    
    assert actual_fields == expected_fields, f"Expected only {expected_fields}, but got {actual_fields}"


@pytest.mark.asyncio
async def test_api_version_method_not_allowed(http_service, register_core_plugin):
    """
    Test that only GET method is allowed on /api/version.
    Other methods should return 405 Method Not Allowed.
    """
    app = http_service.fastapi_app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        # POST should not be allowed
        response = await client.post("/api/version")
        assert response.status_code == 405
        
        # PUT should not be allowed
        response = await client.put("/api/version")
        assert response.status_code == 405
        
        # DELETE should not be allowed
        response = await client.delete("/api/version")
        assert response.status_code == 405
