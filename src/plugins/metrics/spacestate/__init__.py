__display_name__ = "Space State Metrics"
__description__ = "A plugin to expose bucketed space state metrics as JSON for Grafana."
__author__ = "Sam Cork"

import logging
from datetime import datetime, UTC, timedelta
from pprint import pformat
from typing import Annotated, TYPE_CHECKING, cast

from beanie.odm.interfaces.find import FindInterface
from fastapi import Query, HTTPException
from pydantic import BaseModel

from smib.db.manager import DatabaseManager
from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface

if TYPE_CHECKING:
    from spacestate.models import SpaceStateEventHistory

logger = logging.getLogger(__display_name__)

ALLOWED_BUCKET_SIZES = {15, 30}
DEFAULT_DATE_RANGE_DAYS = 28
MIN_DATE_DIFFERENCE_DAYS = 7


class SpaceStateMetricsResponse(BaseModel):
    timestamp: datetime
    open: bool


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
    ) -> list[dict]:
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

        results = await build_weekly_bucket(start, end, bucket_minutes)

        return results

    async def build_weekly_bucket(start: datetime, end: datetime, size: int) -> list[dict]:
        SpaceStateEventHistoryModel = cast(
            "type[SpaceStateEventHistory]",
            database.find_model_by_name("SpaceStateEventHistory"),
        )

        event_query = SpaceStateEventHistoryModel.find(
            SpaceStateEventHistoryModel.timestamp >= start,
            SpaceStateEventHistoryModel.timestamp <= end,
        ).sort("timestamp")

        logger.info(f"Querying SpaceStateEventHistory for events between {start} and {end}")
        logger.debug(f"Found {await event_query.count()} events")

        async for event in event_query:
            logger.debug(
            f"Event: {event.timestamp} - "
            f"Requested State: {event.requested_state} - "
            f"New State: {event.new_state} - "
            f"Requested Duration: {event.requested_duration_seconds}"
        )

        return []