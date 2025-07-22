import secrets

from pydantic import computed_field, SecretStr, Field

from ._env_base_settings import EnvBaseSettings

class WebserverSettings(EnvBaseSettings):
    host: str = "0.0.0.0"
    port: int = 80
    path_prefix: str = "/api"
    forwarded_allow_ips: list[str] = ["*",]
    log_request_details: bool = False

    model_config = {
        "env_prefix": "SMIB_WEBSERVER_"
    }