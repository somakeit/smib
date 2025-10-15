from datetime import timedelta
from typing import Annotated, TypeVar
from pydantic import BaseModel, Field, AfterValidator

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

BaseModel_T = TypeVar("BaseModel_T", bound=BaseModel)