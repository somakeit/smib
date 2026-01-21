__display_name__ = "Space State Metrics"
__description__ = "A plugin to push space state metrics (heatmap) to InfluxDB."
__author__ = "Sam Cork"

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from beanie import SortDirection
from beanie.odm.queries.find import FindMany

from plugins.metrics.common import config as metrics_config
from smib.db.manager import DatabaseManager
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from .config import config

if TYPE_CHECKING:
    from plugins.space.spacestate.models import SpaceStateEventHistory

logger = logging.getLogger(__display_name__)

def register(schedule: ScheduledEventInterface, database: DatabaseManager):
    if not metrics_config.enabled:
        logger.info("Metrics are disabled. Skipping.")
        return

    _SpaceStateEventHistory: type["SpaceStateEventHistory"] | None = None

    async def get_unsynced_events() -> FindMany["SpaceStateEventHistory"]:
        # noinspection PyComparisonWithNone
        return _SpaceStateEventHistory.find(
            _SpaceStateEventHistory.metrics_exported_at == None
        ).sort(("timestamp", SortDirection.ASCENDING))

    async def push_iterator_to_influx(iterator: FindMany["SpaceStateEventHistory"]) -> list["SpaceStateEventHistory"]:
        """ Pairs Open/Close events and handles stale timeouts for the heatmap """
        from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
        from influxdb_client import Point, WritePrecision
        from plugins.space.spacestate.models import SpaceStateEnum, SpaceStateEventHistory

        events_processed: list[SpaceStateEventHistory] = []
        points: list[Point] = []
        active_open: SpaceStateEventHistory | None = None

        async for event in iterator:
            if event.new_state == SpaceStateEnum.OPEN:
                if active_open is None:
                    active_open = event
                else:
                    # Redundant OPEN: Mark as processed to ignore in future runs
                    events_processed.append(event)
            elif event.new_state == SpaceStateEnum.CLOSED:
                if active_open:
                    points.append(Point("space_state").tag("source", active_open.source.value).field("status", 1).time(active_open.timestamp, WritePrecision.NS))
                    points.append(Point("space_state").tag("source", event.source.value).field("status", 0).time(event.timestamp, WritePrecision.NS))
                    events_processed.append(active_open)
                    events_processed.append(event)
                    active_open = None
                else:
                    points.append(Point("space_state").tag("source", event.source.value).field("status", 0).time(event.timestamp, WritePrecision.NS))
                    events_processed.append(event)

        # Handle stale open (Forgotten close)
        if active_open:
            max_seconds = active_open.requested_duration_seconds or (8 * 60 * 60)
            if datetime.now(UTC) > (active_open.timestamp + timedelta(seconds=max_seconds)):
                expiry_time = active_open.timestamp + timedelta(seconds=max_seconds)
                points.append(Point("space_state").tag("source", active_open.source.value).field("status", 1).time(active_open.timestamp, WritePrecision.NS))
                points.append(Point("space_state").tag("source", "timeout_expiry").field("status", 0).time(expiry_time, WritePrecision.NS))
                events_processed.append(active_open)
                logger.info(f"Timed out stale open event from {active_open.timestamp}")

        if points:
            async with InfluxDBClientAsync(url=metrics_config.influx_url, token=metrics_config.influx_token.get_secret_value(), org=metrics_config.influx_org) as client:
                await client.write_api().write(bucket=metrics_config.influx_bucket, record=points)
        
        return events_processed

    @schedule.job("interval", seconds=config.monitor_interval.total_seconds())
    async def monitor_spacestate_event_history_for_new_metrics():
        nonlocal _SpaceStateEventHistory
        if _SpaceStateEventHistory is None:
            _SpaceStateEventHistory = database.find_model_by_name("SpaceStateEventHistory")

        unsynced_iterator = await get_unsynced_events()
        count = await unsynced_iterator.count()
        logger.debug(f"Found {count} unsynced events")
        if count == 0:
            logger.info("No new events to export")
            return

        try:
            processed_events = await push_iterator_to_influx(unsynced_iterator)
            if processed_events:
                now = datetime.now(UTC)
                for event in processed_events:
                    event.metrics_exported_at = now
                    await event.save()
                logger.info(f"Exported {len(processed_events)} events to InfluxDB")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
