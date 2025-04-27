import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from smib.events.services.scheduled_event_service import ScheduledEventService


def test_scheduled_event_service_init():
    """Test ScheduledEventService initialization."""
    # Create service
    service = ScheduledEventService()

    # Verify results
    assert service.logger is not None


def test_scheduler_lazy_property():
    """Test scheduler lazy property."""
    # Create service
    service = ScheduledEventService()

    # Access property
    scheduler = service.scheduler

    # Verify results
    assert isinstance(scheduler, AsyncIOScheduler)


@pytest.mark.asyncio
async def test_start():
    """Test start method."""
    # Create service
    service = ScheduledEventService()
    
    # Mock scheduler
    service.scheduler = MagicMock(spec=AsyncIOScheduler)

    # Call method
    await service.start()

    # Verify results
    service.scheduler.start.assert_called_once()


@pytest.mark.asyncio
async def test_stop():
    """Test stop method."""
    # Create service
    service = ScheduledEventService()
    
    # Mock scheduler
    service.scheduler = MagicMock(spec=AsyncIOScheduler)

    # Call method
    await service.stop()

    # Verify results
    service.scheduler.remove_all_jobs.assert_called_once()
    service.scheduler.shutdown.assert_called_once()