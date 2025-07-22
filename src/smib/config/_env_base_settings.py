from pydantic_settings import BaseSettings



class EnvBaseSettings(BaseSettings):
    model_config = {
        "env_prefix": "SMIB_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }