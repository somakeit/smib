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
