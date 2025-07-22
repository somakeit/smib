import logging
import logging.config
from smib.utilities.environment import is_running_in_docker

def get_logging_config(log_level: str = "DEBUG") -> dict:
    return {
        "version": 1,
        "disable_existing_loggers": False,  # Keeps existing loggers intact unless redefined here
        "formatters": {
            "default": {
                "class": "smib.logging_.utc_formatter.UTCFormatter",
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
            },
            # Docker format has no timestamp, as docker records this separately anyway
            "docker": {
                "format": "[%(levelname)s] [%(name)s]: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "docker" if is_running_in_docker() else "default",
                "level": log_level,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": {
            "smib": {
                "level": "DEBUG"
            },
            "Config Init": {
              "level": "DEBUG"
            },
            "slack_bolt": {
                "level": "WARNING",
                "propagate": False
            },
            "slack_sdk": {
                "level": "WARNING",
                "propagate": False
            },
            "asyncio": {
                "level": "WARNING"
            },
            "pymongo": {
                "level": "WARNING"
            }
        },
    }

def initialise_logging(log_level: str) -> None:
    logging.config.dictConfig(get_logging_config(log_level))
