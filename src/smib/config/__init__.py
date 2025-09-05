import logging as logging_lib
import sys
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel

from pydantic import ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from smib.config.general import GeneralSettings
from smib.config.logging_ import LoggingSettings
from smib.config.project import ProjectSettings
from smib.config.slack import SlackSettings
from smib.config.database import DatabaseSettings
from smib.config.webserver import WebserverSettings
from smib.config._env_base_settings import EnvBaseSettings

from smib.logging_ import initialise_logging

__all__ = [
    "logging",
    "project",
    "general",
    "slack",
    "database",
    "webserver",
    "EnvBaseSettings",
]

_logger = logging_lib.getLogger(__name__)


def _format_validation_errors(collected: list[tuple[BaseModel, ValidationError]]) -> str:
    message_lines: list[str] = []
    for model, validation_errors in collected:
        model_config = model.model_config
        env_var_prefix = model_config.get('env_prefix', '')

        message_lines.append(f"Validation error for {model.__name__}:")
        for error in validation_errors.errors():
            field_name = error["loc"][0]
            field: FieldInfo = model.model_fields[field_name]
            error_message = error["msg"]
            error_type = error["type"]
            provided_value = error["input"]

            message_lines.append(f"\t• {field_name}:")

            spacing = 30
            message_lines.append(f"\t\t{"Error:":<{spacing}} {error_message}")
            if error_type != 'missing' and provided_value != PydanticUndefined:
                message_lines.append(f"\t\t{"Provided Value:":<{spacing}} {provided_value}")

            if field.description:
                message_lines.append(f"\t\t{"Setting Description:":<{spacing}} {field.description}")

            message_lines.append(f"\t\t{"Setting Environment Variable:":<{spacing}} {env_var_prefix}{field_name.upper()}")

            message_lines.append(f"\t\t{"Setting Type:":<{spacing}} {getattr(field.annotation, '__name__', str(field.annotation))}")
            if field.default != PydanticUndefined:
                message_lines.append(f"\t\t{"Setting Default:":<{spacing}} {field.default}")

    return "\n".join(["He's dead, Jim 🖖"] + message_lines)

# Attempt to initialise all settings immediately (import-time), but with
# clear, user-friendly validation reporting and fail-fast behaviour.
_collected_errors: List[Tuple[type[BaseModel] | None, ValidationError]] = []

logging: LoggingSettings | None = None
try:
    logging = LoggingSettings()
    initialise_logging(logging.log_level)
    _logger = logging_lib.getLogger(__name__)
except ValidationError as ve:
    _collected_errors.append((LoggingSettings, ve))

project: ProjectSettings | None = None
general: GeneralSettings | None = None
slack: SlackSettings | None = None
database: DatabaseSettings | None = None
webserver: WebserverSettings | None = None

try:
    project = ProjectSettings()
except ValidationError as ve:
    _collected_errors.append((ProjectSettings, ve))

try:
    general = GeneralSettings()
except ValidationError as ve:
    _collected_errors.append((GeneralSettings, ve))

try:
    slack = SlackSettings()
except ValidationError as ve:
    _collected_errors.append((SlackSettings, ve))

try:
    database = DatabaseSettings()
except ValidationError as ve:
    _collected_errors.append((DatabaseSettings, ve))

try:
    webserver = WebserverSettings()
except ValidationError as ve:
    _collected_errors.append((WebserverSettings, ve))

if _collected_errors:
    # Prefer printing to stderr to ensure visibility even if logging isn't configured yet
    msg = _format_validation_errors(_collected_errors)
    # Print to stderr only to avoid duplicate outputs (some environments route logs to stderr too)
    _logger.error(msg)
    # Exit early so the application clearly stops on config errors
    raise SystemExit(1)
else:
    _logger.debug(f"Logging Settings Initialised:\n{logging.model_dump_json(indent=2)}")
    _logger.debug(f"Project Settings Initialised:\n{project.model_dump_json(indent=2)}")
    _logger.debug(f"General Settings Initialised:\n{general.model_dump_json(indent=2)}")
    _logger.debug(f"Slack Settings Initialised:\n{slack.model_dump_json(indent=2)}")
    _logger.debug(f"Database Settings Initialised:\n{database.model_dump_json(indent=2)}")
    _logger.debug(f"Webserver Settings Initialised:\n{webserver.model_dump_json(indent=2)}")





