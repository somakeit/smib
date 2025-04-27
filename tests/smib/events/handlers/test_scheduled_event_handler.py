import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apscheduler.job import Job
from slack_bolt import BoltResponse
from slack_bolt.request.async_request import AsyncBoltRequest

from smib.events.handlers import BoltRequestMode
from smib.events.handlers.scheduled_event_handler import (
    ScheduledEventHandler,
    to_async_bolt_request,
)


@pytest.mark.asyncio
async def test_scheduled_event_handler_handle():
    """Test ScheduledEventHandler.handle method."""
    # Create mocks
    mock_bolt_app = AsyncMock()
    mock_bolt_app.async_dispatch = AsyncMock(return_value=BoltResponse(status=200, body="OK"))

    mock_job = MagicMock(spec=Job)
    mock_job.__slots__ = ['id', 'name', 'trigger', 'executor', 'func', 'args', 'kwargs', 'misfire_grace_time', 
                          'coalesce', 'max_instances', 'next_run_time', '_jobstore_alias', '_scheduler', '_modify_lock']
    mock_job.id = "job-123"
    mock_job.name = "test-job"

    # Create handler
    handler = ScheduledEventHandler(bolt_app=mock_bolt_app)

    # Call handle method
    with patch("smib.events.handlers.scheduled_event_handler.to_async_bolt_request", new_callable=AsyncMock) as mock_to_bolt_request:
        mock_bolt_request = AsyncMock(spec=AsyncBoltRequest)
        mock_to_bolt_request.return_value = mock_bolt_request

        result = await handler.handle(mock_job)

        # Verify results
        mock_to_bolt_request.assert_called_once_with(mock_job)
        mock_bolt_app.async_dispatch.assert_called_once_with(mock_bolt_request)
        assert result == mock_bolt_app.async_dispatch.return_value


@pytest.mark.asyncio
async def test_to_async_bolt_request():
    """Test to_async_bolt_request function."""
    # Create mock job
    mock_job = MagicMock(spec=Job)
    mock_job.__slots__ = ['id', 'name', 'trigger', 'executor', 'func', 'args', 'kwargs', 'misfire_grace_time', 
                          'coalesce', 'max_instances', 'next_run_time', '_jobstore_alias', '_scheduler', '_modify_lock']
    mock_job.id = "job-123"
    mock_job.name = "test-job"
    mock_job.trigger = "cron"
    mock_job.executor = "default"
    mock_job.func = lambda: None
    mock_job.args = []
    mock_job.kwargs = {}
    mock_job.misfire_grace_time = 1
    mock_job.coalesce = True
    mock_job.max_instances = 1
    mock_job.next_run_time = None

    # Call function
    result = await to_async_bolt_request(mock_job)

    # Verify results
    assert isinstance(result, AsyncBoltRequest)
    assert result.body["type"] == "event_callback"
    assert result.body["event"]["type"] == "scheduled_job"

    # Check job dictionary
    job_dict = result.body["event"]["job"]
    assert job_dict["id"] == "job-123"
    assert job_dict["name"] == "test-job"
    assert job_dict["trigger"] == "cron"
    assert job_dict["executor"] == "default"
    assert job_dict["args"] == []
    assert job_dict["kwargs"] == {}
    assert job_dict["misfire_grace_time"] == 1
    assert job_dict["coalesce"] is True
    assert job_dict["max_instances"] == 1
    assert job_dict["next_run_time"] is None

    # Check other properties
    assert result.mode == BoltRequestMode.SCHEDULED
    assert "job" in result.context
    assert result.context["job"] == mock_job
