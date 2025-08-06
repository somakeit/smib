from datetime import datetime
from datetime import UTC
from typing import Any, Annotated

from fastapi import Header

DeviceHostnameHeader = Annotated[str, Header(
    description="Hostname of S.M.I.B.H.I.D. device",
    example="SMIBHID-DUMMY"
)]


def validate_timestamp(value: Any) -> Any:
    """ Validate a timestamp."""
    if isinstance(value, (int, float)):
        try:
            datetime.fromtimestamp(value, UTC)
            return value
        except (OverflowError, OSError, ValueError):
            raise ValueError("Invalid Unix timestamp")
    raise ValueError("Timestamp must be an integer or float representing Unix time")