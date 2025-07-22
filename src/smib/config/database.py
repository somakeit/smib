from pydantic import computed_field, SecretStr, Field

from ._env_base_settings import EnvBaseSettings
from .project import ProjectSettings

class DatabaseSettings(EnvBaseSettings):
    mongo_db_host: str = "localhost"
    mongo_db_port: int = 27017
    mongo_db_name: str = Field(default_factory=lambda: ProjectSettings().name)

    @computed_field
    @property
    def mongo_db_uri(self) -> str:
        return f"mongodb://{self.mongo_db_host}:{self.mongo_db_port}"

    model_config = {
        "env_prefix": "SMIB_DB_"
    }

if __name__ == "__main__":
    print(DatabaseSettings().model_dump_json(indent=2))