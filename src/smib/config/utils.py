import logging as logging_lib
from collections import defaultdict
from types import UnionType
from typing import Optional, get_origin, Union, get_args, Annotated, Literal

from pydantic import ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from smib.config._types import BaseSettings_T, CollectedErrors_T
from smib.utilities import split_camel_case

CONSTRAINT_LABELS = {
    "gt": "Greater Than",
    "ge": "Greater Than Or Equal",
    "lt": "Less Than",
    "le": "Less Than Or Equal",
    "multiple_of": "Multiple Of",
    "min_length": "Minimum Length",
    "max_length": "Maximum Length",
    "pattern": "Pattern",
}


def get_field_constraints(field: FieldInfo) -> list[tuple[str, object]]:
    constraints: list[tuple[str, object]] = []

    for metadata in field.metadata:
        for attribute_name, label in CONSTRAINT_LABELS.items():
            value = getattr(metadata, attribute_name, None)

            if value is not None:
                constraints.append((label, value))

    return constraints


def select_provided_value(values: list[object]) -> object | None:
    if not values:
        return None

    unique_values = list(dict.fromkeys(values))

    if len(unique_values) == 1:
        return unique_values[0]

    return max(unique_values, key=lambda value: len(str(value)))


def select_failed_value(values: list[object], provided_value: object | None) -> object | None:
    if provided_value is None:
        return None

    unique_values = list(dict.fromkeys(values))
    failed_values = [
        value
        for value in unique_values
        if value != provided_value
    ]

    if not failed_values:
        return None

    return min(failed_values, key=lambda value: len(str(value)))


def is_union_field(field: FieldInfo) -> bool:
    return get_origin(field.annotation) in (Union, type(Union[str, int]))

def format_type_annotation(annotation: object) -> str:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Annotated:
        annotation_type, *metadata = args
        formatted_metadata = ", ".join(type(item).__name__ for item in metadata)
        return f"Annotated[{format_type_annotation(annotation_type)}, {formatted_metadata}]"

    if origin in (Union, UnionType) or isinstance(annotation, UnionType):
        return " | ".join(format_type_annotation(arg) for arg in args)

    if origin is Literal:
        return "Literal[" + ", ".join(repr(arg) for arg in args) + "]"

    if origin is list:
        return f"list[{format_type_annotation(args[0])}]" if args else "list"

    if origin is not None:
        formatted_args = ", ".join(format_type_annotation(arg) for arg in args)
        origin_name = getattr(origin, "__name__", str(origin).replace("typing.", ""))
        return f"{origin_name}[{formatted_args}]"

    if hasattr(annotation, "__name__"):
        return annotation.__name__

    return str(annotation).replace("typing.", "")


def format_validation_errors(collected: CollectedErrors_T) -> str:
    message_lines: list[str] = []
    for model, validation_errors in collected:
        model_config = model.model_config
        env_var_prefix = model_config.get('env_prefix', '')

        grouped_errors = defaultdict(list)
        for error in validation_errors.errors():
            grouped_errors[error["loc"][0]].append(error)

        message_lines.append(f"Validation error for {model.__name__}:")
        for field_name, errors in grouped_errors.items():
            field: FieldInfo = model.model_fields[field_name]
            provided_values = [
                error["input"]
                for error in errors
                if error["type"] != "missing" and error["input"] != PydanticUndefined
            ]

            message_lines.append(f"\t• {field_name}:")

            spacing = 30
            if len(errors) == 1:
                message_lines.append(f"\t\t{"Error:":<{spacing}} {errors[0]["msg"]}")
            elif is_union_field(field):
                message_lines.append(f"\t\tError (Input value should match one of these supported formats):")
                for error in errors:
                    message_lines.append(f"\t\t\t• {error["msg"]}")
            else:
                message_lines.append(f"\t\t{"Errors:":<{spacing}}")
                for error in errors:
                    message_lines.append(f"\t\t\t• {error["msg"]}")

            provided_value = select_provided_value(provided_values)
            failed_value = select_failed_value(provided_values, provided_value)

            if provided_value is not None:
                message_lines.append(f"\t\t{"Provided Value:":<{spacing}} {provided_value}")

            if failed_value is not None:
                message_lines.append(f"\t\t{"Failed Value:":<{spacing}} {failed_value}")

            if field.description:
                message_lines.append(f"\t\t{"Setting Description:":<{spacing}} {field.description}")

            constraints = get_field_constraints(field)
            if constraints:
                constraint_spacing = max(len(label) for label, _ in constraints) + 3
                message_lines.append(f"\t\t{"Setting Constraints:":<{spacing}}")
                for label, value in constraints:
                    message_lines.append(f"\t\t\t• {f"{label}:":<{constraint_spacing}} {value}")

            message_lines.append(f"\t\t{"Setting Environment Variable:":<{spacing}} {env_var_prefix}{field_name.upper()}")

            message_lines.append(f"\t\t{"Setting Type:":<{spacing}} {format_type_annotation(field.annotation)}")
            if field.default != PydanticUndefined:
                message_lines.append(f"\t\t{"Setting Default:":<{spacing}} {field.default}")

            if field.examples:
                message_lines.append(f"\t\t{"Setting Examples:":<{spacing}}")
                for example in field.examples:
                    message_lines.append(f"\t\t\t• {example}")

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
        logger.error(format_validation_errors(errors))
        raise AssertionError('Invalid configuration') from errors[0][1]

    logger.debug(f"{" ".join(split_camel_case(settings.__class__.__name__))} Initialised:\n{settings.model_dump_json(indent=2)}")
    return settings

