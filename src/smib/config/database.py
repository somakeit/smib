from pydantic import computed_field, SecretStr, Field

from ._env_base_settings import EnvBaseSettings
from .project import ProjectSettings

class DatabaseSettings(EnvBaseSettings):
    mongo_db_host: str = Field(
        default="localhost",
        description="MongoDB server hostname or IP address"
    )
    mongo_db_port: int = Field(
        default=27017,
        description="MongoDB server port number"
    )
    mongo_db_name: str = Field(
        default_factory=lambda: ProjectSettings().name,
        description="MongoDB database name, defaults to the project name"
    )

    @computed_field
    @property
    def mongo_db_uri(self) -> str:
        return f"mongodb://{self.mongo_db_host}:{self.mongo_db_port}"

    model_config = {
        "env_prefix": "SMIB_DB_"
    }

if __name__ == "__main__":
    print(DatabaseSettings().model_dump_json(indent=2))
