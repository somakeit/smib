from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError
import datetime

tz_name = "Europe/London" # Replace with your desired timezone
try:
    tz = ZoneInfo(tz_name)
    print(f"'{tz_name}' is a valid timezone.")
except ZoneInfoNotFoundError:
    print(f"'{tz_name}' is NOT a valid timezone.")

from tzlocal import get_localzone

iana_timezone = get_localzone().key
print(iana_timezone)  # Example output: "Europe/London"
