import logging as logging_lib
from smib.config.general import GeneralSettings
from smib.config.logging_ import LoggingSettings
from smib.config.project import ProjectSettings
from smib.config.slack import SlackSettings
from smib.config.database import DatabaseSettings
from smib.config.webserver import WebserverSettings
from smib.config._env_base_settings import EnvBaseSettings

__all__ = ["logging", "project", "general", "slack", "database", "webserver", "EnvBaseSettings"]

from smib.logging_ import initialise_logging

_logger = logging_lib.getLogger(__name__)

try:
    logging = LoggingSettings()
    initialise_logging(logging.log_level)
    project = ProjectSettings()
    general = GeneralSettings()
    slack = SlackSettings()
    database = DatabaseSettings()
    webserver = WebserverSettings()
except Exception as e:
    _logger.exception(repr(e), exc_info=e)
else:
    _logger.debug(f"Logging Settings Initialised:\n{logging.model_dump_json(indent=2)}")
    _logger.debug(f"Project Settings Initialised:\n{project.model_dump_json(indent=2)}")
    _logger.debug(f"General Settings Initialised:\n{general.model_dump_json(indent=2)}")
    _logger.debug(f"Slack Settings Initialised:\n{slack.model_dump_json(indent=2)}")
    _logger.debug(f"Database Settings Initialised:\n{database.model_dump_json(indent=2)}")
    _logger.debug(f"Webserver Settings Initialised:\n{webserver.model_dump_json(indent=2)}")





