from pydantic_settings import BaseSettings



class EnvBaseSettings(BaseSettings):
    model_config = {
        "env_prefix": "SMIB_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }
    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls,
            init_settings,
            file_secret_settings,
            dotenv_settings,
            env_settings,
    ):
        return env_settings, dotenv_settings, file_secret_settings