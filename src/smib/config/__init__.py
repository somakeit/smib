import logging as logging_lib

from smib.config._env_base_settings import EnvBaseSettings
from smib.config._types import IntervalField, BaseSettings_T, CollectedErrors_T
from smib.config.database import DatabaseSettings
from smib.config.environment import EnvironmentSettings
from smib.config.general import GeneralSettings
from smib.config.logging_ import LoggingSettings
from smib.config.project import ProjectSettings
from smib.config.slack import SlackSettings
from smib.config.utils import format_validation_errors, init_settings
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
    "environment",
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

_environment: EnvironmentSettings | None = init_settings(EnvironmentSettings, _collected_errors)
_project: ProjectSettings | None = init_settings(ProjectSettings, _collected_errors)
_general: GeneralSettings | None = init_settings(GeneralSettings, _collected_errors)
_slack: SlackSettings | None = init_settings(SlackSettings, _collected_errors)
_database: DatabaseSettings | None = init_settings(DatabaseSettings, _collected_errors)
_webserver: WebserverSettings | None = init_settings(WebserverSettings, _collected_errors)

if _collected_errors:
    # Log to stderr only to avoid duplicate outputs (some environments route logs to stderr too)
    _logger.error(format_validation_errors(_collected_errors))

    # Exit early so the application clearly stops on config errors
    raise SystemExit(1)

assert logging is not None
assert _environment is not None
assert _project is not None
assert _general is not None
assert _slack is not None
assert _database is not None
assert _webserver is not None

environment: EnvironmentSettings = _environment
project: ProjectSettings = _project
general: GeneralSettings = _general
slack: SlackSettings = _slack
database: DatabaseSettings = _database
webserver: WebserverSettings = _webserver

for setting in [logging, environment, project, general, slack, database, webserver]:
    _logger.debug(f"{" ".join(split_camel_case(setting.__class__.__name__))} Initialised:\n{setting.model_dump_json(indent=2)}")