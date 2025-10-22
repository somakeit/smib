import pytest
from httpx import AsyncClient

from smib.config.project import ProjectSettings
from smib.config.webserver import WebserverSettings


@pytest.fixture(autouse=True, scope="module")
def webserver_settings() -> WebserverSettings:
    """Fixture to provide the webserver settings."""
    from smib.config import webserver
    return webserver

@pytest.fixture(autouse=True, scope="module")
def project_settings() -> ProjectSettings:
    """Fixture to provide the webserver URL."""
    from smib.config import project
    return project

@pytest.fixture(autouse=True, scope="module")
def api_client(webserver_settings: WebserverSettings) -> AsyncClient:
    """Fixture to provide an API client for testing."""
    url = f"http://{webserver_settings.host}:{webserver_settings.port}/{webserver_settings.path_prefix.rstrip('/')}"
    return AsyncClient(base_url=url, follow_redirects=True)

@pytest.mark.asyncio
async def test_api_ping(api_client: AsyncClient, project_settings: ProjectSettings):
    """Test the ping endpoint."""
    resp = await api_client.get('/api/ping')
    assert resp.status_code == 200
    assert resp.json() == {"ping": "pong"}

    assert resp.headers['x-app-name'] == project_settings.name
    assert resp.headers['x-app-version'] == project_settings.version

@pytest.mark.asyncio
async def test_api_version(api_client: AsyncClient, project_settings: ProjectSettings):
    """Test the version endpoint."""
    resp = await api_client.get('/api/version')
    assert resp.status_code == 200

    resp_json = resp.json()
    assert resp_json.has_key('smib')

    assert resp_json['smib'] == project_settings.version
    assert resp_json.has_key('mongo')

    assert resp.headers['x-app-name'] == project_settings.name
    assert resp.headers['x-app-version'] == project_settings.version