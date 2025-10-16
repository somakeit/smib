import logging as logging_lib

from smib.config._env_base_settings import EnvBaseSettings
from smib.config._types import IntervalField, BaseSettings_T, CollectedErrors_T
from smib.config.utils import format_validation_errors, init_settings
from smib.config.database import DatabaseSettings
from smib.config.general import GeneralSettings
from smib.config.logging_ import LoggingSettings
from smib.config.project import ProjectSettings
from smib.config.slack import SlackSettings
from smib.config.webserver import WebserverSettings
from smib.logging_ import initialise_logging
from smib.utilities import split_camel_case

__all__ = [
    "logging",
    "project",
    "general",
    "slack",
    "database",
    "webserver",
    "EnvBaseSettings",
    "IntervalField",
    "format_validation_errors",
    "init_settings",
    "BaseSettings_T",
    "CollectedErrors_T"
]

# Attempt to initialise all settings immediately (import-time), but with
# clear, user-friendly validation reporting and fail-fast behaviour.
_collected_errors: CollectedErrors_T = []
_logger = logging_lib.getLogger(__name__)

logging: LoggingSettings | None = init_settings(LoggingSettings, _collected_errors)
if logging is not None:
    initialise_logging(logging.log_level)
    _logger = logging_lib.getLogger(__name__)

project: ProjectSettings | None = init_settings(ProjectSettings, _collected_errors)
general: GeneralSettings | None = init_settings(GeneralSettings, _collected_errors)
slack: SlackSettings | None = init_settings(SlackSettings, _collected_errors)
database: DatabaseSettings | None = init_settings(DatabaseSettings, _collected_errors)
webserver: WebserverSettings | None = init_settings(WebserverSettings, _collected_errors)

print(_collected_errors)
print(logging, project, general, slack, database, webserver)

if _collected_errors:
    msg = format_validation_errors(_collected_errors)

    # Print to stderr only to avoid duplicate outputs (some environments route logs to stderr too)
    _logger.error(msg)

    # Exit early so the application clearly stops on config errors
    raise SystemExit(1)
else:
    for setting in [logging, project, general, slack, database, webserver]:
        _logger.debug(f"{" ".join(split_camel_case(setting.__class__.__name__))} Initialised:\n{setting.model_dump_json(indent=2)}")
