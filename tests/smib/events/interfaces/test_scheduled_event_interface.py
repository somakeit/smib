import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from slack_bolt.app.async_app import AsyncApp

from smib.events.handlers.scheduled_event_handler import ScheduledEventHandler
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from smib.events.services.scheduled_event_service import ScheduledEventService


def test_scheduled_event_interface_init():
    """Test ScheduledEventInterface initialization."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=ScheduledEventHandler)
    mock_service = MagicMock(spec=ScheduledEventService)

    # Create interface
    interface = ScheduledEventInterface(bolt_app=mock_bolt_app, handler=mock_handler, service=mock_service)

    # Verify results
    assert interface.bolt_app == mock_bolt_app
    assert interface.handler == mock_handler
    assert interface.service == mock_service
    assert interface.logger is not None


@pytest.mark.asyncio
@patch("smib.events.interfaces.scheduled_event_interface.unicodedata")
async def test_job_decorator(mock_unicodedata):
    """Test job decorator."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=ScheduledEventHandler)
    mock_service = MagicMock(spec=ScheduledEventService)
    mock_scheduler = MagicMock(spec=AsyncIOScheduler)
    mock_service.scheduler = mock_scheduler

    # Mock unicodedata.normalize
    mock_unicodedata.normalize.return_value = "Normalized Test Func"

    # Create interface
    interface = ScheduledEventInterface(bolt_app=mock_bolt_app, handler=mock_handler, service=mock_service)

    # Create a test function
    async def test_func():
        """Test function docstring."""
        return "test result"

    # Mock the job
    mock_job = MagicMock(spec=Job)
    mock_scheduler.get_job.return_value = mock_job

    # Call the decorator
    decorator = interface.job(trigger="cron", hour=12)
    result = decorator(test_func)

    # Verify results
    assert result == test_func
    mock_scheduler.add_job.assert_called_once()

    # Verify add_job arguments
    args, kwargs = mock_scheduler.add_job.call_args
    assert args[1] == "cron"  # trigger
    assert kwargs["id"] == "test_func"
    assert kwargs["name"] == "Test function docstring."
    assert kwargs["hour"] == 12

    # Verify bolt_app.event was called
    mock_bolt_app.event.assert_called_once_with('scheduled_job', matchers=[mock_bolt_app.event.call_args[1]['matchers'][0]])
    mock_bolt_app.event.return_value.assert_called_once_with(test_func)


@pytest.mark.asyncio
async def test_job_wrapper_execution():
    """Test the job wrapper execution."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=ScheduledEventHandler)
    mock_handler.handle = AsyncMock()
    mock_service = MagicMock(spec=ScheduledEventService)
    mock_scheduler = MagicMock(spec=AsyncIOScheduler)
    mock_service.scheduler = mock_scheduler

    # Create interface
    interface = ScheduledEventInterface(bolt_app=mock_bolt_app, handler=mock_handler, service=mock_service)
    interface.logger = MagicMock()

    # Create a test function
    async def test_func():
        return "test result"

    # Mock the job
    mock_job = MagicMock(spec=Job)
    mock_scheduler.get_job.return_value = mock_job

    # Call the decorator
    decorator = interface.job(trigger="cron", hour=12)
    decorated_func = decorator(test_func)

    # Extract the wrapper function
    wrapper_func = mock_scheduler.add_job.call_args[0][0]

    # Call the wrapper function
    await wrapper_func()

    # Verify handler.handle was called
    mock_handler.handle.assert_called_once_with(mock_job)


@pytest.mark.asyncio
async def test_job_wrapper_handles_exceptions():
    """Test the job wrapper handles exceptions."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=ScheduledEventHandler)
    mock_handler.handle = AsyncMock(side_effect=KeyboardInterrupt("Test interrupt"))
    mock_service = MagicMock(spec=ScheduledEventService)
    mock_scheduler = MagicMock(spec=AsyncIOScheduler)
    mock_service.scheduler = mock_scheduler

    # Create interface
    interface = ScheduledEventInterface(bolt_app=mock_bolt_app, handler=mock_handler, service=mock_service)
    interface.logger = MagicMock()

    # Create a test function
    async def test_func():
        return "test result"

    # Mock the job
    mock_job = MagicMock(spec=Job)
    mock_scheduler.get_job.return_value = mock_job

    # Call the decorator
    decorator = interface.job(trigger="cron", hour=12)
    decorated_func = decorator(test_func)

    # Extract the wrapper function
    wrapper_func = mock_scheduler.add_job.call_args[0][0]

    # Call the wrapper function
    await wrapper_func()

    # Verify handler.handle was called
    mock_handler.handle.assert_called_once_with(mock_job)

    # Verify logger.info was called with the exception
    interface.logger.info.assert_called_once()
    assert "received termination" in interface.logger.info.call_args[0][0]
    assert "KeyboardInterrupt" in interface.logger.info.call_args[0][0]


@pytest.mark.asyncio
async def test_job_matcher():
    """Test the job matcher function."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=ScheduledEventHandler)
    mock_service = MagicMock(spec=ScheduledEventService)
    mock_scheduler = MagicMock(spec=AsyncIOScheduler)
    mock_service.scheduler = mock_scheduler

    # Create interface
    interface = ScheduledEventInterface(bolt_app=mock_bolt_app, handler=mock_handler, service=mock_service)

    # Create a test function
    async def test_func():
        return "test result"

    # Mock the job
    mock_job = MagicMock(spec=Job)
    mock_scheduler.get_job.return_value = mock_job

    # Call the decorator
    decorator = interface.job(trigger="cron", id="custom-id", hour=12)
    decorated_func = decorator(test_func)

    # Extract the matcher function
    matcher_func = mock_bolt_app.event.call_args[1]['matchers'][0]

    # Test matcher with matching event
    event = {"job": {"id": "custom-id"}}
    result = await matcher_func(event)
    assert result is True

    # Test matcher with non-matching event
    event = {"job": {"id": "different-id"}}
    result = await matcher_func(event)
    assert result is False


def test_job_id_and_name_generation():
    """Test job ID and name generation."""
    # Create mocks
    mock_bolt_app = MagicMock(spec=AsyncApp)
    mock_handler = MagicMock(spec=ScheduledEventHandler)
    mock_service = MagicMock(spec=ScheduledEventService)
    mock_scheduler = MagicMock(spec=AsyncIOScheduler)
    mock_service.scheduler = mock_scheduler

    # Create interface
    interface = ScheduledEventInterface(bolt_app=mock_bolt_app, handler=mock_handler, service=mock_service)

    # Test with explicit ID and name
    @interface.job(trigger="cron", id="explicit-id", name="Explicit Name", hour=12)
    async def test_func1():
        """Test function 1."""
        pass

    mock_scheduler.add_job.assert_called_with(
        mock_scheduler.add_job.call_args[0][0],
        "cron",
        id="explicit-id",
        name="Explicit Name",
        misfire_grace_time=mock_scheduler.add_job.call_args[1]["misfire_grace_time"],
        coalesce=mock_scheduler.add_job.call_args[1]["coalesce"],
        max_instances=mock_scheduler.add_job.call_args[1]["max_instances"],
        next_run_time=mock_scheduler.add_job.call_args[1]["next_run_time"],
        hour=12
    )

    # Reset mock
    mock_scheduler.reset_mock()

    # Test with docstring as name
    @interface.job(trigger="cron", hour=12)
    async def test_func2():
        """Custom docstring."""
        pass

    assert mock_scheduler.add_job.call_args[1]["id"] == "test_func2"
    assert mock_scheduler.add_job.call_args[1]["name"] == "Custom docstring."

    # Reset mock
    mock_scheduler.reset_mock()

    # Test with normalized function name
    with patch("smib.events.interfaces.scheduled_event_interface.unicodedata.normalize") as mock_normalize:
        mock_normalize.return_value = "Normalized Name"

        @interface.job(trigger="cron", hour=12)
        async def test_func3():
            pass

        assert mock_scheduler.add_job.call_args[1]["id"] == "test_func3"
        assert mock_scheduler.add_job.call_args[1]["name"] == "Normalized Name"
        mock_normalize.assert_called_with('NFKD', "test_func3".replace('_', ' ').title())
