import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

from apscheduler.job import Job
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from smib.plugins.integrations.scheduled_plugin_integration import ScheduledPluginIntegration


@pytest.fixture
def mock_scheduled_event_interface():
    """Fixture for a mocked ScheduledEventInterface."""
    mock_interface = MagicMock(spec=ScheduledEventInterface)
    mock_interface.service = MagicMock()
    mock_interface.service.scheduler = MagicMock()
    return mock_interface


@pytest.fixture
def scheduled_plugin_integration(mock_scheduled_event_interface):
    """Fixture for a ScheduledPluginIntegration instance."""
    return ScheduledPluginIntegration(mock_scheduled_event_interface)


class TestScheduledPluginIntegration:
    """Tests for the ScheduledPluginIntegration class."""

    def test_init(self, scheduled_plugin_integration, mock_scheduled_event_interface):
        """Test initialization of ScheduledPluginIntegration."""
        assert scheduled_plugin_integration.scheduled_event_interface == mock_scheduled_event_interface
        assert isinstance(scheduled_plugin_integration.logger, object)

    def test_disconnect_plugin_no_jobs(self, scheduled_plugin_integration):
        """Test disconnect_plugin when there are no jobs."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        scheduled_plugin_integration.scheduled_event_interface.service.scheduler.get_jobs.return_value = []

        # Execute
        scheduled_plugin_integration.disconnect_plugin(mock_plugin)

        # Verify
        scheduled_plugin_integration.scheduled_event_interface.service.scheduler.get_jobs.assert_called_once()
        scheduled_plugin_integration.scheduled_event_interface.service.scheduler.remove_job.assert_not_called()

    def test_disconnect_plugin_with_jobs(self, scheduled_plugin_integration):
        """Test disconnect_plugin when there are jobs to remove."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        # Create a mock job
        mock_job = MagicMock(spec=Job)
        mock_job.id = "test_job_id"
        mock_job.func.__module__ = "test_module"
        sys.modules["test_module"] = MagicMock()
        sys.modules["test_module"].__file__ = "/path/to/plugin/job.py"

        scheduled_plugin_integration.scheduled_event_interface.service.scheduler.get_jobs.return_value = [mock_job]

        # Mock Path.resolve and is_relative_to
        with patch('smib.plugins.integrations.scheduled_plugin_integration.Path') as mock_path_class:
            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.is_relative_to.return_value = True
            mock_path_instance.name = "__init__.py"
            mock_path_instance.parent = MagicMock(spec=Path)

            # Execute
            scheduled_plugin_integration.disconnect_plugin(mock_plugin)

            # Verify
            scheduled_plugin_integration.scheduled_event_interface.service.scheduler.get_jobs.assert_called_once()
            scheduled_plugin_integration.scheduled_event_interface.service.scheduler.remove_job.assert_called_once_with(mock_job.id)

    def test_disconnect_plugin_with_non_matching_jobs(self, scheduled_plugin_integration):
        """Test disconnect_plugin when there are jobs but none match the plugin."""
        # Setup
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "test_plugin"
        mock_plugin.__file__ = "/path/to/plugin/__init__.py"

        # Create a mock job
        mock_job = MagicMock(spec=Job)
        mock_job.id = "test_job_id"
        mock_job.func.__module__ = "test_module"
        sys.modules["test_module"] = MagicMock()
        sys.modules["test_module"].__file__ = "/path/to/other/job.py"

        scheduled_plugin_integration.scheduled_event_interface.service.scheduler.get_jobs.return_value = [mock_job]

        # Mock Path.resolve and is_relative_to
        with patch('smib.plugins.integrations.scheduled_plugin_integration.Path') as mock_path_class:
            mock_path_instance = MagicMock(spec=Path)
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.resolve.return_value = mock_path_instance
            mock_path_instance.is_relative_to.return_value = False
            mock_path_instance.name = "__init__.py"
            mock_path_instance.parent = MagicMock(spec=Path)

            # Execute
            scheduled_plugin_integration.disconnect_plugin(mock_plugin)

            # Verify
            scheduled_plugin_integration.scheduled_event_interface.service.scheduler.get_jobs.assert_called_once()
            scheduled_plugin_integration.scheduled_event_interface.service.scheduler.remove_job.assert_not_called()