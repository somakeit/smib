import re
from datetime import datetime, timedelta

import pytz
from humanize import naturaltime, precisedelta


def get_humanized_time(timestamp: datetime) -> str:
    """Convert timestamp to human-readable format.
    Example: "2 minutes ago", "5 hours ago", etc.

    Args:
        timestamp: The datetime to humanize (can be naive or timezone-aware)
    """

    # Ensure timestamp is timezone-aware
    if timestamp.tzinfo is None:
        timestamp = pytz.UTC.localize(timestamp)

    # Get current time in UTC
    now = datetime.now(pytz.UTC)

    return naturaltime(now - timestamp)

def get_humanized_timedelta(delta: timedelta) -> str:
    """Convert timedelta to human-readable format.
    Example: "2 minutes", "5 hours", etc.

    Args:
        timedelta: The timedelta to humanize
    """
    return precisedelta(delta)

def split_camel_case(text: str) -> list[str]:
    """Split a CamelCase string into words, handling consecutive capitals."""
    # Insert space before uppercase letters that follow lowercase letters
    text = re.sub('([a-z])([A-Z])', r'\1 \2', text)
    # Insert space before uppercase letter followed by lowercase (for acronyms)
    text = re.sub('([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
    return text.split()