import logging
import logging.config

from smib.config import ROOT_LOG_LEVEL

# Logger configuration in dictConfig format
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # Keeps existing loggers intact unless redefined here
    "formatters": {
        "default": {
            "format": "[%(asctime)s][%(levelname)s][%(name)s]: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
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
        }
    },
}

def initialise_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
