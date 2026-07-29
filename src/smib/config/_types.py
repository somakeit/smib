from datetime import timedelta
from pathlib import PurePosixPath
from typing import Annotated, TypeVar, Literal

from pydantic import AfterValidator, ValidationError, BeforeValidator, ValidateAs, IPvAnyAddress, IPvAnyNetwork
from pydantic_settings import BaseSettings, NoDecode


def _ensure_timedelta(value: int | timedelta) -> timedelta:
    """Normalize int or timedelta to timedelta with optional validation."""
    if isinstance(value, int):
        value = timedelta(seconds=value)
    elif not isinstance(value, timedelta):
        raise TypeError(f"Expected int or timedelta, got {type(value).__name__}")

    return value

IntervalField = Annotated[
    int | timedelta,
    AfterValidator(_ensure_timedelta),
]

BaseSettings_T = TypeVar("BaseSettings_T", bound=BaseSettings)
CollectedErrors_T = list[tuple[type[BaseSettings], ValidationError]]


def _split_csv(v: object) -> list[str] | object:
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    return v

def validate_path_prefix(value: str) -> str:
    if not value.startswith("/"):
        raise ValueError("Path prefix must start with '/'")

    if any(character.isspace() for character in value):
        raise ValueError("Path prefix must not contain whitespace")

    path = PurePosixPath(value)

    if str(path) != value:
        raise ValueError(f"Path prefix must be normalized as '{path}'")

    if value != "/" and value.endswith("/"):
        raise ValueError("Path prefix must not end with '/' unless it is the root path '/'")

    return value


type CSV[T] = Annotated[list[T], NoDecode, BeforeValidator(_split_csv)]

type ValidatedNetworkHostStr = Annotated[
    str, ValidateAs(IPvAnyAddress | IPvAnyNetwork | Literal["localhost"], str)
]

type ValidatedIPvAnyAddress = Annotated[
    str, ValidateAs(IPvAnyAddress, str)
]

type PathPrefix = Annotated[
    str, AfterValidator(validate_path_prefix)
]