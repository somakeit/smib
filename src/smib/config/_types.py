from datetime import timedelta
from typing import Annotated, TypeVar

from pydantic import AfterValidator, ValidationError
from pydantic_settings import BaseSettings


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