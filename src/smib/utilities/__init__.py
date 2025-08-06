from humanize import naturaltime
from datetime import datetime, UTC
import pytz

def get_humanized_time(timestamp: datetime) -> str:
    """Convert timestamp to human readable format.
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
