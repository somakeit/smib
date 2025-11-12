import pytest
import pytest_asyncio
from httpx import AsyncClient

from smib.config.project import ProjectSettings
from smib.config.webserver import WebserverSettings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def webserver_settings() -> WebserverSettings:
    """Provide instantiated webserver settings."""
    from smib.config.webserver import WebserverSettings
    return WebserverSettings()


@pytest.fixture(scope="module")
def project_settings() -> ProjectSettings:
    """Provide instantiated project settings."""
    from smib.config.project import ProjectSettings
    return ProjectSettings()


@pytest_asyncio.fixture(scope="function")
async def api_client(webserver_settings: WebserverSettings) -> AsyncClient:
    """
    Provide an AsyncClient for testing.
    Each test gets its own event loop, preventing 'Event loop is closed' errors.
    """
    # Build a clean base URL regardless of trailing slashes
    prefix = webserver_settings.path_prefix.strip("/")
    base_url = f"http://{webserver_settings.host}:{webserver_settings.port}"
    if prefix:
        base_url = f"{base_url}/{prefix}"

    async with AsyncClient(base_url=base_url, follow_redirects=True) as client:
        yield client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_ping(api_client: AsyncClient):
    """Test the ping endpoint."""
    resp = await api_client.get("/api/ping")
    assert resp.status_code == 200
    assert resp.json().get("ping") == "pong"


@pytest.mark.asyncio
async def test_api_version(api_client: AsyncClient, project_settings: ProjectSettings):
    """Test the version endpoint."""
    resp = await api_client.get("/api/version")
    assert resp.status_code == 200

    data = resp.json()
    assert "smib" in data
    assert data["smib"] == project_settings.version
    assert "mongo" in data

    # Use .get() to avoid KeyErrors, headers are case-insensitive
    assert resp.headers.get("x-app-name") == project_settings.name
    assert resp.headers.get("x-app-version") == project_settings.version


# Additional tests start here

@pytest.mark.asyncio
async def test_api_health(api_client: AsyncClient):
    """
    Test the health endpoint.
    Expected behavior:
    - Status code: 200
    - Response JSON includes { "status": "healthy" }
    """
    resp = await api_client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"


@pytest.mark.asyncio
async def test_api_404_not_found(api_client: AsyncClient):
    """
    Test for unknown endpoints.
    Expected behavior:
    - Status code: 404
    - Response JSON includes { "detail": "Not Found" }
    """
    resp = await api_client.get("/api/unknown-endpoint")
    assert resp.status_code == 404
    data = resp.json()
    assert data.get("detail") == "Not Found"


@pytest.mark.asyncio
async def test_static_files_access(api_client: AsyncClient):
    """
    Test that the /static endpoint is accessible for static files.
    - Ensure response code is 200 or 404 (depending on file existence).
    """
    resp = await api_client.get("/static/example.png")
    assert resp.status_code in (200, 404)  # 200 if file exists, otherwise 404
    if resp.status_code == 200:
        assert "image/png" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_api_documents_endpoints(api_client: AsyncClient):
    """
    Test the auto-generated API documentation endpoints.
    - Ensure Swagger and ReDoc documentation are accessible.
    """
    swagger_resp = await api_client.get("/api/docs")
    redoc_resp = await api_client.get("/api/redoc")

    assert swagger_resp.status_code == 200
    assert "text/html" in swagger_resp.headers["content-type"]

    assert redoc_resp.status_code == 200
    assert "text/html" in redoc_resp.headers["content-type"]


@pytest.mark.asyncio
async def test_api_authentication_required_endpoint(api_client: AsyncClient):
    """
    Test an endpoint that requires authentication (if applicable).
    - Ensure a 401 Unauthorized response if no auth token is provided.
    """
    resp = await api_client.get("/api/restricted-endpoint")
    assert resp.status_code == 401
    data = resp.json()
    assert "detail" in data
    assert data["detail"] == "Unauthorized"

# Edge case tests

@pytest.mark.asyncio
async def test_api_invalid_method(api_client: AsyncClient):
    """
    Test that invalid methods are correctly handled with 405 Method Not Allowed.
    Example: POST request to a GET-only endpoint.
    """
    resp = await api_client.post("/api/ping")
    assert resp.status_code == 405
    assert resp.json().get("detail") == "Method Not Allowed"


@pytest.mark.asyncio
async def test_api_malformed_data(api_client: AsyncClient):
    """
    Test that the server handles malformed data gracefully.
    Example: Try to send invalid JSON payload to a POST endpoint.
    """
    resp = await api_client.post("/api/example-post-endpoint", json={"invalid": "data"})
    assert resp.status_code in (400, 422)  # Typically 400 Bad Request or 422 Unprocessable Entity


@pytest.mark.asyncio
async def test_api_long_route(api_client: AsyncClient):
    """
    Test the server response to overly long URLs.
    Expected behavior:
    - The response should not crash the server.
    - Status code should be 404 or appropriate.
    """
    long_path = "/api/" + "longpath" * 50
    resp = await api_client.get(long_path)
    assert resp.status_code in (404, 414)  # 414 URI Too Long, or 404 Not Found


# End-to-End Tests (if applicable, assuming core functionalities)

@pytest.mark.asyncio
async def test_api_spacestate(api_client: AsyncClient):
    """
    Test for the current space state API.
    - Ensure it returns latest data or correct default state.
    """
    resp = await api_client.get("/api/spacestate")
    assert resp.status_code == 200
    data = resp.json()
    assert "state" in data  # Check the key exists
    assert isinstance(data["state"], str)  # Validate type


@pytest.mark.asyncio
async def test_api_smibhid_log(api_client: AsyncClient):
    """
    Test the SMIBHID button press log API.
    - Validate response schema and status.
    """
    resp = await api_client.get("/api/smibhid/log")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)  # Assume the output is a list of logs
    if data:
        assert "timestamp" in data[0]  # Check schema of first item (e.g., timestamp field)
        assert "event" in data[0]


@pytest.mark.asyncio
async def test_api_smibhid_no_logs(api_client: AsyncClient):
    """
    Test SMIBHID API with no log entries.
    - Ensure the response handles an empty state gracefully.
    """
    resp = await api_client.get("/api/smibhid/log")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)  # Output should still be a list
    assert len(data) == 0  # Assume no logs initially


