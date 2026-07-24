from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class WeeklyBucketMetadata(BaseModel):
    requested_start: Annotated[datetime, Field(description="Requested start timestamp for the query")]
    requested_end: Annotated[datetime, Field(description="Requested end timestamp for the query")]
    event_start: Annotated[datetime | None, Field(description="Timestamp of the first event used in the response")]
    event_end: Annotated[datetime | None, Field(description="Timestamp of the last event used in the response")]
    bucket_minutes: Annotated[int, Field(description="Bucket size in minutes")]


class WeeklyBucketData(BaseModel):
    weekday: Annotated[str, Field(description="Weekday name for this bucket, Monday through Sunday")]
    weekday_index: Annotated[int, Field(description="Weekday index, where Monday is 0 and Sunday is 6", ge=0, le=6)]
    time: Annotated[str, Field(description="Bucket start time in HH:MM format")]
    time_index: Annotated[int, Field(description="Bucket start time in minutes since midnight", ge=0, le=1439)]
    bucket_minutes: Annotated[int, Field(description="Bucket size in minutes")]
    open_seconds: Annotated[int, Field(description="Total calculated open seconds in this weekly bucket", ge=0)]
    open_minutes: Annotated[float, Field(description="Total calculated open minutes in this weekly bucket", ge=0)]
    open_ratio: Annotated[float, Field(description="Ratio of calculated open time to possible open time for this weekly bucket", ge=0, le=1)]


class WeeklyBucketResult(BaseModel):
    metadata: Annotated[WeeklyBucketMetadata, Field(description="Metadata describing the query and event coverage")]
    buckets: Annotated[list[WeeklyBucketData], Field(description="Canonical Monday-to-Sunday weekly heatmap buckets")]