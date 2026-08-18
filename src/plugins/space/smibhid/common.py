from datetime import UTC
from datetime import datetime
from typing import Any, Annotated

from fastapi import Header
from pydantic import BeforeValidator, Field

DeviceHostnameHeader = Annotated[str, Header(
    description="Hostname of S.M.I.B.H.I.D. device",
    json_schema_extra={"example":"SMIBHID-DUMMY"}
)]


def validate_timestamp(value: Any) -> Any:
    """ Validate a timestamp."""
    if isinstance(value, (int, float)):
        try:
            datetime.fromtimestamp(value, UTC)
            return value
        except (OverflowError, OSError, ValueError):
            raise ValueError("Invalid Unix timestamp")
    elif isinstance(value, datetime):
        return value.timestamp()

    elif isinstance(value, str):
        try:
            return datetime.fromisoformat(value).timestamp()
        except ValueError:
            raise ValueError("Invalid ISO 8601 timestamp")

    raise ValueError("Timestamp must be a UNIX epoch timestamp, or an ISO 8601 timestamp string")

def get_timestamp(value: int | float) -> datetime:
    return datetime.fromtimestamp(value, UTC)

SMIBHIDTimestamp = Annotated[
    int | float,
    Field(
        description="Timestamp",
        examples=[int(datetime.now(UTC).timestamp()), "2023-07-01T12:00:00Z"],
        # int|float is the true post-validation type; the schema is overridden here, so the API
        # docs still show ISO 8601 strings as accepted input (validate_timestamp converts them).
        json_schema_extra={"anyOf": [{"type": "integer"}, {"type": "number"}, {"type": "string"}]},
    ),
    BeforeValidator(validate_timestamp),
]