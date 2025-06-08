import logging
import logging.config

from smib.config import ROOT_LOG_LEVEL
from smib.utilities.environment import is_running_in_docker

# Logger configuration in dictConfig format
LOGGING_CONFIG = {
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
            "level": ROOT_LOG_LEVEL,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": ROOT_LOG_LEVEL,
    },
    "loggers": {
        "smib": {
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

def initialise_logging() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
