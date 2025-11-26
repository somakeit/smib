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
    match resp.status_code:
        case 200:
            assert resp.headers.get("content-type") == "image/png"
        case 404:
            assert resp.json().get("detail") == "File not found"

@pytest.mark.asyncio
async def test_api_documents_endpoints(api_client: AsyncClient):
    """
    Test the auto-generated API documentation endpoints.
    - Ensure Swagger and ReDoc documentation are accessible.
    """
    swagger_resp = await api_client.get("/api/docs")
    redoc_resp = await api_client.get("/api/redoc")
    database_resp = await api_client.get("/database/docs")

    assert swagger_resp.status_code == 200
    assert "text/html" in swagger_resp.headers["content-type"]

    assert redoc_resp.status_code == 200
    assert "text/html" in redoc_resp.headers["content-type"]

    assert database_resp.status_code == 200
    assert "text/html" in database_resp.headers["content-type"]


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
async def test_api_spacestate(api_client: AsyncClient):
    """
    Test for the current space state API.
    - Ensure it returns latest data or correct default state.
    """
    resp = await api_client.get("/api/space/state")
    assert resp.status_code == 200
    data = resp.json()
    assert "open" in data  # Check the key exists
    assert isinstance(data["open"], bool)  # Validate type

#


