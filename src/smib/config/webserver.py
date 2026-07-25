from typing import Literal

from pydantic import Field

from ._env_base_settings import EnvBaseSettings
from ._types import CSV, ValidatedIPvAnyAddress, PathPrefix


class WebserverSettings(EnvBaseSettings):
    host: str = Field(
        default="0.0.0.0",
        description="Host address to bind the webserver to (0.0.0.0 for all interfaces)",
        examples=["0.0.0.0", "127.0.0.1"]
    )
    port: int = Field(
        default=80,
        description="Port number for the webserver to listen on",
        examples=[80, 8080],
        le=65535,
        ge=1
    )
    path_prefix: PathPrefix = Field(
        default="/",
        description="URL path prefix for the API endpoints",
        examples=["/", "/smib"]
    )
    forwarded_allow_ips: CSV[ValidatedIPvAnyAddress] | Literal["*"] = Field(
        default="*",
        description="List of IPs allowed for X-Forwarded-For headers (* for all)",
        examples=["127.0.0.1,192.168.1.3", "*", "127.0.0.1"],
        validate_default=False
    )
    log_request_details: bool = Field(
        default=False,
        description="Whether to log detailed information about HTTP requests"
    )

    model_config = {
        "env_prefix": "SMIB_WEBSERVER_"
    }
