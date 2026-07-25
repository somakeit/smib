__display_name__ = "Space State Metrics"
__description__ = "A plugin to expose bucketed space state metrics as JSON for Grafana."
__author__ = "Sam Cork"

import logging
from collections import defaultdict
from datetime import datetime, UTC, timedelta
from pprint import pformat
from typing import Annotated

from fastapi import Query, HTTPException

from plugins.space.spacestate.models import SpaceStateEnum, SpaceStateEventHistory
from smib.db.manager import DatabaseManager
from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from .models import WeeklyBucketData, WeeklyBucketResult, WeeklyBucketMetadata

logger = logging.getLogger(__display_name__)

ALLOWED_BUCKET_SIZES = {15, 30}
DEFAULT_DATE_RANGE_DAYS = 28
MIN_DATE_DIFFERENCE_DAYS = 7
DEFAULT_OPEN_HOURS = 8
MAX_OPEN_HOURS = 16
DEFAULT_OPEN_DURATION = timedelta(hours=DEFAULT_OPEN_HOURS)
MAX_OPEN_DURATION = timedelta(hours=MAX_OPEN_HOURS)


def register(api: ApiEventInterface, database: DatabaseManager):
    @api.get("/metrics/spacestate/weekly-bucket")
    async def get_weekly_bucket(
            start: Annotated[
                datetime | None,
                Query(description="Start timestamp for the accumulation period (ISO 8601 format)", example="2023-01-01T00:00:00Z"),
            ] = None,
            end: Annotated[
                datetime | None,
                Query(description="End timestamp for the accumulation period (ISO 8601 format)", example="2023-01-08T00:00:00Z"),
            ] = None,
            bucket_minutes: Annotated[
                int,
                Query(description="Bucket size in minutes. Supported values: 15, 30", example=15),
            ] = 15,
    ) -> WeeklyBucketResult:
        new = datetime.now(UTC)
        end = end or new
        start = start or new - timedelta(days=DEFAULT_DATE_RANGE_DAYS)

        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        if end.tzinfo is None:
            end = end.replace(tzinfo=UTC)

        if bucket_minutes not in ALLOWED_BUCKET_SIZES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid bucket size: {bucket_minutes}. Supported values: {ALLOWED_BUCKET_SIZES}",
            )

        if start >= end:
            raise HTTPException(status_code=400, detail="Start timestamp must be before end timestamp")

        if end - start < timedelta(days=MIN_DATE_DIFFERENCE_DAYS):
            raise HTTPException(
                status_code=400,
                detail=f"Date range must be at least {MIN_DATE_DIFFERENCE_DAYS} days",
            )

        logger.debug(f"Getting weekly bucket for {start} to {end} with bucket size {bucket_minutes} minutes")

        result = await build_weekly_bucket(start, end, bucket_minutes)

        return result

    async def build_weekly_bucket(start: datetime, end: datetime, size: int) -> WeeklyBucketResult:
        """
        Build a canonical Monday-to-Sunday weekly profile of calculated open time.

        The requested time range is treated as a source interval containing individual
        space-state events. Events are processed in timestamp order to reconstruct
        non-overlapping open intervals. An open event starts an interval only if one
        is not already active. A later close event ends the active interval. If no
        close event appears before the requested or default fallback close time, the
        interval is automatically closed at that fallback time. Open intervals are
        also capped by a maximum open duration to prevent unrealistically long spans.

        Closed-event durations are intentionally ignored, because they are
        informational and should not reduce or extend calculated open time.

        Each derived open interval is clipped to the requested ``start``/``end`` range,
        then split across fixed-size time buckets. Buckets are keyed by weekday index
        and minute-of-day rather than by calendar date, so multiple Mondays at 19:00
        within the returned data range all accumulate into the same weekly bucket.

        Open ratios are calculated against the possible bucket time between the first
        and last returned event timestamps, not the full requested range. This prevents
        sparse or over-wide queries from diluting the heatmap intensity.

        The returned list always contains a complete week, Monday through Sunday, with
        every bucket for each day included. Buckets with no calculated open time are
        returned with zero seconds/minutes so consumers can render a stable grid.
        """
        SpaceStateEventHistoryModel: type[SpaceStateEventHistory] = database.find_model_by_name("SpaceStateEventHistory")

        event_query = SpaceStateEventHistoryModel.find(
            SpaceStateEventHistoryModel.timestamp >= start,
            SpaceStateEventHistoryModel.timestamp <= end,
            ).sort("timestamp")

        logger.info(f"Querying SpaceStateEventHistory for events between {start} and {end}")
        logger.debug(f"Found {await event_query.count()} events")

        bucket_size = timedelta(minutes=size)
        bucket_seconds = int(bucket_size.total_seconds())
        buckets: dict[tuple[int, int], int] = defaultdict(int)
        possible_bucket_seconds: dict[tuple[int, int], int] = defaultdict(int)
        events = await event_query.to_list()

        def floor_to_bucket(timestamp: datetime) -> datetime:
            midnight = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_since_midnight = int((timestamp - midnight).total_seconds())
            floored_seconds = seconds_since_midnight - (seconds_since_midnight % bucket_seconds)
            return midnight + timedelta(seconds=floored_seconds)

        def add_possible_interval(interval_start: datetime, interval_end: datetime) -> None:
            cursor = floor_to_bucket(interval_start)

            while cursor < interval_end:
                next_bucket = cursor + bucket_size
                overlap_start = max(interval_start, cursor)
                overlap_end = min(interval_end, next_bucket)

                if overlap_start < overlap_end:
                    weekday = cursor.weekday()
                    minute_of_day = cursor.hour * 60 + cursor.minute
                    possible_bucket_seconds[(weekday, minute_of_day)] += int((overlap_end - overlap_start).total_seconds())

                cursor = next_bucket

        def add_open_interval(interval_start: datetime, interval_end: datetime) -> None:
            interval_start = max(interval_start, start)
            interval_end = min(interval_end, end)

            if interval_start >= interval_end:
                return

            cursor = floor_to_bucket(interval_start)

            while cursor < interval_end:
                next_bucket = cursor + bucket_size
                overlap_start = max(interval_start, cursor)
                overlap_end = min(interval_end, next_bucket)

                if overlap_start < overlap_end:
                    weekday = cursor.weekday()
                    minute_of_day = cursor.hour * 60 + cursor.minute
                    buckets[(weekday, minute_of_day)] += int((overlap_end - overlap_start).total_seconds())

                cursor = next_bucket

        if events:
            add_possible_interval(events[0].timestamp, events[-1].timestamp)

        current_open_started_at: datetime | None = None
        current_open_fallback_closed_at: datetime | None = None
        current_open_max_closed_at: datetime | None = None

        for event in events:
            current_open_closed_at = (
                min(
                    close_at
                    for close_at in (current_open_fallback_closed_at, current_open_max_closed_at)
                    if close_at is not None
                )
                if current_open_started_at is not None
                else None
            )

            if (
                    current_open_started_at is not None
                    and current_open_closed_at is not None
                    and event.timestamp >= current_open_closed_at
            ):
                add_open_interval(current_open_started_at, current_open_closed_at)
                current_open_started_at = None
                current_open_fallback_closed_at = None
                current_open_max_closed_at = None

            if event.new_state == SpaceStateEnum.OPEN:
                event_fallback_closed_at = event.timestamp + (
                    timedelta(seconds=event.requested_duration_seconds)
                    if event.requested_duration_seconds
                    else DEFAULT_OPEN_DURATION
                )

                if current_open_started_at is None:
                    current_open_started_at = event.timestamp
                    current_open_fallback_closed_at = event_fallback_closed_at
                    current_open_max_closed_at = event.timestamp + MAX_OPEN_DURATION
                else:
                    current_open_fallback_closed_at = max(
                        current_open_fallback_closed_at or event_fallback_closed_at,
                        event_fallback_closed_at,
                        )

                continue

            if event.new_state == SpaceStateEnum.CLOSED and current_open_started_at is not None:
                add_open_interval(current_open_started_at, event.timestamp)
                current_open_started_at = None
                current_open_fallback_closed_at = None
                current_open_max_closed_at = None

        if current_open_started_at is not None:
            current_open_closed_at = min(
                close_at
                for close_at in (current_open_fallback_closed_at, current_open_max_closed_at)
                if close_at is not None
            )
            add_open_interval(current_open_started_at, current_open_closed_at)

        results = [
            WeeklyBucketData(
                weekday_index=weekday,
                time_index=minute_of_day,
                bucket_minutes=size,
                open_seconds=buckets[(weekday, minute_of_day)],
                total_bucket_seconds=possible_bucket_seconds[(weekday, minute_of_day)],
            )
            for weekday in range(7)
            for minute_of_day in range(0, 24 * 60, size)
            if events
        ]

        result = WeeklyBucketResult(
            metadata=WeeklyBucketMetadata(
                requested_start=start,
                requested_end=end,
                event_start=events[0].timestamp if events else None,
                event_end=events[-1].timestamp if events else None,
                bucket_minutes=size,
                total_events_processed=len(events),
            ),
            buckets=results,
        )

        logger.debug(f"Built weekly bucket:\n{pformat(result)}")

        return result