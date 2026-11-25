"""
Push realistic multi-device sensor data at a local SMIB instance.

Posts through the real HTTP API rather than writing to Mongo directly, so the ingest path,
validation and unit upsert all get exercised the same way a real S.M.I.B.H.I.D. would exercise
them. Useful for seeing /howfresh, the app home and the sensor log monitor behave with more
than one device reporting, which is otherwise hard to produce locally.

Seeds the two devices in the space, plus an optional long-silent third to exercise the
staleness handling:

  SMIBHID-FAN       clean room, full sensor suite, relay metrics, reporting now
  SMIBHID-WORKSHOP  light only (temperature and particulate still to be fitted)
  SMIBHID-SPARE     a week stale, only with --include-stale

Usage:
    python scripts/seed_local_sensor_data.py                      # both real devices, 2h history
    python scripts/seed_local_sensor_data.py --hours 24
    python scripts/seed_local_sensor_data.py --include-stale      # adds the silent device
    python scripts/seed_local_sensor_data.py --dry-run            # print, send nothing

The target defaults to http://localhost, which is where compose publishes the proxy.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta

DEFAULT_BASE_URL = "http://localhost"

SENSOR_LOG_PATH = "/api/smibhid/log/sensor"
LIGHT_STATE_PATH = "/api/space/light/state"
RELAY_STATE_PATH = "/api/space/relay/state"

# Reporting cadence. Real SMIBHIDs push a batch of readings every minute; a coarser interval
# keeps the seeded volume sane over a long window while still looking like a real feed.
READING_INTERVAL = timedelta(minutes=5)

LIGHT_THRESHOLD_LUX = 500.0


class Device:
    """A device to seed, and the shape of the data it reports."""

    def __init__(
        self,
        hostname: str,
        *,
        sensors: list[str],
        silent_for: timedelta = timedelta(0),
        light_base: float,
        temperature_base: float | None = None,
        reports_relay: bool = False,
    ):
        self.hostname = hostname
        self.sensors = sensors
        # How long ago this device stopped reporting - 0 means it is reporting right now.
        self.silent_for = silent_for
        self.light_base = light_base
        self.temperature_base = temperature_base
        self.reports_relay = reports_relay


DEVICES = [
    Device(
        "SMIBHID-FAN",
        sensors=["BH1750", "BME280", "SCD30", "PMSA003I", "InternalMetrics"],
        light_base=310.0,
        temperature_base=21.4,
        reports_relay=True,
    ),
    Device(
        "SMIBHID-WORKSHOP",
        sensors=["BH1750"],
        light_base=180.0,
    ),
]

STALE_DEVICE = Device(
    "SMIBHID-SPARE",
    sensors=["BH1750", "BME280"],
    silent_for=timedelta(days=9),
    light_base=95.0,
    temperature_base=16.2,
)

UNITS = {
    "BH1750": {"light": "lx"},
    "BME280": {"temperature": "C", "humidity": "%", "pressure": "hPa"},
    "SCD30": {"co2": "ppm", "temperature": "C", "relative_humidity": "%"},
    "PMSA003I": {
        "pm10_standard": "ug/m3",
        "pm25_standard": "ug/m3",
        "pm100_standard": "ug/m3",
        "pm10_env": "ug/m3",
        "pm25_env": "ug/m3",
        "pm100_env": "ug/m3",
        "particles_03um": "count/0.1L",
        "particles_05um": "count/0.1L",
        "particles_10um": "count/0.1L",
        "particles_25um": "count/0.1L",
        "particles_50um": "count/0.1L",
        "particles_100um": "count/0.1L",
    },
    "InternalMetrics": {"relay_on_time": "s"},
}


def daily_light_curve(timestamp: datetime, base: float) -> float:
    """
    Rough daylight shape, so a long history does not read as a flat line.

    Peaks early afternoon and bottoms out overnight. Not meant to be physically accurate -
    just enough variation that charts and averages have something to show.
    """
    hour = timestamp.hour + timestamp.minute / 60
    daylight = max(0.0, math.sin((hour - 6) / 12 * math.pi))
    return round(base * (0.1 + 1.6 * daylight) + random.uniform(-8, 8), 2)


def wander(base: float, spread: float, *, low: float | None = None) -> float:
    value = base + random.uniform(-spread, spread)
    if low is not None:
        value = max(low, value)
    return round(value, 2)


def build_readings(device: Device, timestamp: datetime, relay_on_time: int) -> dict:
    data: dict[str, dict[str, float | int]] = {}

    if "BH1750" in device.sensors:
        data["BH1750"] = {"light": daily_light_curve(timestamp, device.light_base)}

    if "BME280" in device.sensors and device.temperature_base is not None:
        data["BME280"] = {
            "temperature": wander(device.temperature_base, 0.6),
            "humidity": wander(42.0, 3.0, low=0.0),
            "pressure": wander(1013.2, 2.5),
        }

    if "SCD30" in device.sensors and device.temperature_base is not None:
        data["SCD30"] = {
            "temperature": wander(device.temperature_base + 0.5, 0.6),
            "relative_humidity": wander(41.0, 3.0, low=0.0),
            # CO2 climbs while the space is occupied, so track working hours loosely.
            "co2": wander(700.0 if 9 <= timestamp.hour <= 22 else 460.0, 60.0, low=400.0),
        }

    if "PMSA003I" in device.sensors:
        fine = random.randint(4, 9)
        data["PMSA003I"] = {
            "pm10_standard": max(0, fine - 1),
            "pm25_standard": fine,
            "pm100_standard": fine,
            "pm10_env": max(0, fine - 1),
            "pm25_env": fine,
            "pm100_env": fine,
            "particles_03um": random.randint(600, 900),
            "particles_05um": random.randint(180, 300),
            "particles_10um": random.randint(20, 45),
            "particles_25um": random.randint(0, 3),
            "particles_50um": 0,
            "particles_100um": 0,
        }

    if "InternalMetrics" in device.sensors:
        data["InternalMetrics"] = {"relay_on_time": relay_on_time}

    return data


def post_json(url: str, payload: dict, *, headers: dict[str, str], method: str = "POST") -> int:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status
    except urllib.error.HTTPError as error:
        # Surface the body - FastAPI validation errors explain exactly which field was
        # rejected, which is the whole reason for going through the API rather than Mongo.
        print(f"  HTTP {error.code} from {method} {url}: {error.read().decode()[:400]}", file=sys.stderr)
        raise


def seed_device(base_url: str, device: Device, *, hours: int, dry_run: bool) -> None:
    now = datetime.now(UTC)
    last_report = now - device.silent_for
    first_report = last_report - timedelta(hours=hours)

    headers = {"X-SMIBHID-Hostname": device.hostname}

    readings = []
    timestamp = first_report
    # Relay on-time accumulates across the window, as the device's own counter would.
    relay_on_time = random.randint(1_700_000, 1_750_000) if device.reports_relay else 0

    while timestamp <= last_report:
        if device.reports_relay and 9 <= timestamp.hour <= 22:
            relay_on_time += int(READING_INTERVAL.total_seconds())

        readings.append(
            {
                "timestamp": int(timestamp.timestamp()),
                "human_timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "data": build_readings(device, timestamp, relay_on_time),
            }
        )
        timestamp += READING_INTERVAL

    units = {sensor: UNITS[sensor] for sensor in device.sensors if sensor in UNITS}

    age = "reporting now" if not device.silent_for else f"last reported {device.silent_for.days}d ago"
    print(f"{device.hostname}: {len(readings)} readings over {hours}h, {age}")

    if dry_run:
        print(f"  sensors: {', '.join(device.sensors)}")
        print(f"  sample:  {json.dumps(readings[-1]['data'], ensure_ascii=False)[:200]}")
        return

    # The sensor log route takes the whole batch in one request, as SMIBHID does.
    post_json(
        f"{base_url}{SENSOR_LOG_PATH}",
        {"readings": readings, "units": units},
        headers=headers,
    )
    print(f"  posted {len(readings)} sensor readings")

    if "BH1750" in device.sensors:
        latest_light = readings[-1]["data"]["BH1750"]["light"]
        post_json(
            f"{base_url}{LIGHT_STATE_PATH}",
            {
                "light_state": latest_light > LIGHT_THRESHOLD_LUX,
                "light_value_lux": latest_light,
                "threshold_lux": LIGHT_THRESHOLD_LUX,
            },
            headers=headers,
            method="PUT",
        )
        print(f"  posted light state ({latest_light} lx)")

    if device.reports_relay:
        post_json(
            f"{base_url}{RELAY_STATE_PATH}",
            {
                "active": True,
                "total_active_seconds": relay_on_time,
                "timestamp": int(last_report.timestamp()),
            },
            headers=headers,
        )
        print(f"  posted relay state (on, {relay_on_time}s total)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"SMIB base URL (default: {DEFAULT_BASE_URL})")
    parser.add_argument("--hours", type=int, default=2, help="Hours of history to seed per device (default: 2)")
    parser.add_argument(
        "--include-stale",
        action="store_true",
        help="Also seed SMIBHID-SPARE, silent for 9 days, to exercise staleness handling",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print what would be sent, send nothing")
    parser.add_argument("--seed", type=int, default=None, help="Seed the RNG for reproducible data")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    devices = [*DEVICES, STALE_DEVICE] if args.include_stale else list(DEVICES)
    base_url = args.base_url.rstrip("/")

    print(f"target: {base_url}{' (dry run)' if args.dry_run else ''}\n")

    for device in devices:
        seed_device(base_url, device, hours=args.hours, dry_run=args.dry_run)
        print()

    if not args.dry_run:
        print("Done. Try /howfresh and /howfresh detailed in Slack.")


if __name__ == "__main__":
    main()
