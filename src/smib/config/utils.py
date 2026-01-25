import logging as logging_lib
from typing import Optional

from pydantic import ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from smib.config._types import BaseSettings_T, CollectedErrors_T
from smib.utilities import split_camel_case


def format_validation_errors(collected: CollectedErrors_T) -> str:
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

def init_settings(
        settings_cls: type[BaseSettings_T],
        collect_errors: CollectedErrors_T | None = None,
) -> Optional[BaseSettings_T]:
    """
    Try to initialise a Pydantic settings class.

    - If `collect_errors` is provided, errors are appended there.
    - Returns the instance or None on failure.
    """
    try:
        return settings_cls()
    except ValidationError as ve:
        if collect_errors is not None:
            collect_errors.append((settings_cls, ve))
        return None

def init_plugin_settings(settings_cls: type[BaseSettings_T], logger: logging_lib.Logger) -> Optional[BaseSettings_T]:
    errors: list[tuple[type[BaseSettings_T], ValidationError]] = []
    settings = init_settings(settings_cls, errors)
    if settings is None:
        logger.debug(f"Failed to initialise {settings_cls.__name__}: {errors}")
        logger.error(format_validation_errors(errors))
        raise AssertionError('Invalid configuration') from errors[0][1]

    logger.debug(f"{" ".join(split_camel_case(settings.__class__.__name__))} Initialised:\n{settings.model_dump_json(indent=2)}")
    return settings

