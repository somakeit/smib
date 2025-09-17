from pydantic import Field

from ._env_base_settings import EnvBaseSettings
from ._env_base_settings import EnvBaseSettings


class WebserverSettings(EnvBaseSettings):
    host: str = Field(
        default="0.0.0.0",
        description="Host address to bind the webserver to (0.0.0.0 for all interfaces)"
    )
    port: int = Field(
        default=80,
        description="Port number for the webserver to listen on"
    )
    path_prefix: str = Field(
        default="/",
        description="URL path prefix for the API endpoints"
    )
    forwarded_allow_ips: list[str] = Field(
        default=["*",],
        description="List of IPs allowed for X-Forwarded-For headers (* for all)"
    )
    log_request_details: bool = Field(
        default=False,
        description="Whether to log detailed information about HTTP requests"
    )

    model_config = {
        "env_prefix": "SMIB_WEBSERVER_"
    }
