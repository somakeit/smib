import calendar
from datetime import datetime, date
from typing import Annotated

from pydantic import BaseModel, Field, computed_field


class WeeklyBucketMetadata(BaseModel):
    requested_start: Annotated[date, Field(description="Requested start date for the query", examples=["2024-01-01"])]
    requested_end: Annotated[date, Field(description="Requested end date for the query", examples=["2024-01-07"])]
    event_start: Annotated[datetime | None, Field(description="Timestamp of the first event used in the response", examples=["2024-01-01T00:00:00Z"])]
    event_end: Annotated[datetime | None, Field(description="Timestamp of the last event used in the response", examples=["2024-01-07T23:59:59Z"])]
    bucket_minutes: Annotated[int, Field(description="Bucket size in minutes", examples=[15, 30])]
    total_events_processed: Annotated[int, Field(description="Total number of events processed for this query", ge=0, examples=[0, 100, 1000])]



class WeeklyBucketData(BaseModel):
    weekday_index: Annotated[int, Field(description="Weekday index, where Monday is 0 and Sunday is 6", ge=0, le=6, examples=[0, 1, 2, 3, 4, 5, 6])]
    time_index: Annotated[int, Field(description="Bucket start time in minutes since midnight", ge=0, le=1439, examples=[0, 15, 30, 60, 120])]
    bucket_minutes: Annotated[int, Field(description="Bucket size in minutes", examples=[15, 30])]
    open_seconds: Annotated[int, Field(description="Total calculated open seconds in this weekly bucket", ge=0, examples=[0, 900, 1800])]
    total_bucket_seconds: Annotated[int, Field(description="Total possible seconds represented by this weekly bucket", ge=0, examples=[900, 1800, 3600])]

    @computed_field(description="Weekday name for this bucket, Monday through Sunday", examples=["monday"])
    @property
    def weekday(self) -> str:
        return calendar.day_name[self.weekday_index].lower()

    @computed_field(description="Bucket start time in HH:MM format", examples=["00:00", "12:30"])
    @property
    def time(self) -> str:
        return f"{self.time_index // 60:02d}:{self.time_index % 60:02d}"

    @computed_field(description="Total calculated open minutes in this weekly bucket", examples=[0, 30, 60])
    @property
    def open_minutes(self) -> float:
        return round(self.open_seconds / 60, 2)

    @computed_field(description="Ratio of calculated open time to possible open time for this weekly bucket", examples=[0.0, 0.5, 1.0])
    @property
    def open_ratio(self) -> float:
        if self.total_bucket_seconds <= 0:
            return 0

        return round(min(self.open_seconds / self.total_bucket_seconds, 1), 4)




class WeeklyBucketResult(BaseModel):
    metadata: Annotated[WeeklyBucketMetadata, Field(description="Metadata describing the query and event coverage")]
    buckets: Annotated[list[WeeklyBucketData], Field(description="Canonical Monday-to-Sunday weekly heatmap buckets")]