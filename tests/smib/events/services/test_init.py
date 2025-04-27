import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

import asyncio
from typing import Protocol

from smib.events.services import EventServiceProtocol, EventServiceManager


class MockEventService:
    """Mock implementation of EventServiceProtocol for testing."""
    def __init__(self):
        # Use internal mocks to track calls
        self._start_mock = MagicMock()
        self._stop_mock = MagicMock()

    async def start(self):
        # Call the mock to track the call, but return a proper awaitable
        self._start_mock()
        return None

    async def stop(self):
        # Call the mock to track the call, but return a proper awaitable
        self._stop_mock()
        return None


def test_event_service_manager_init():
    """Test EventServiceManager initialization."""
    # Create manager
    manager = EventServiceManager()

    # Verify results
    assert manager._services == []
    assert manager.logger is not None


def test_register():
    """Test register method."""
    # Create manager
    manager = EventServiceManager()

    # Create mock services
    service1 = MockEventService()
    service2 = MockEventService()

    # Register services
    manager.register(service1)
    manager.register(service2)

    # Verify results
    assert len(manager._services) == 2
    assert manager._services[0] == service1
    assert manager._services[1] == service2


def test_services_string_property():
    """Test _services_string property."""
    # Create manager
    manager = EventServiceManager()

    # Test with no services
    assert manager._services_string == "None"

    # Create mock services
    service1 = MockEventService()
    service2 = MockEventService()

    # Register services
    manager.register(service1)
    manager.register(service2)

    # Verify results
    assert manager._services_string == "MockEventService, MockEventService"


@pytest.mark.asyncio
async def test_start_all_with_services():
    """Test start_all method with registered services."""
    # Create manager
    manager = EventServiceManager()
    manager.logger = MagicMock()

    # Create mock services
    service1 = MockEventService()
    service2 = MockEventService()

    # Register services
    manager.register(service1)
    manager.register(service2)

    # Call method
    await manager.start_all()

    # Verify results
    service1._start_mock.assert_called_once()
    service2._start_mock.assert_called_once()
    manager.logger.info.assert_called_once_with("Starting 2 service(s) (MockEventService, MockEventService)")


@pytest.mark.asyncio
async def test_start_all_no_services():
    """Test start_all method with no registered services."""
    # Create manager
    manager = EventServiceManager()
    manager.logger = MagicMock()

    # Call method
    await manager.start_all()

    # Verify results
    manager.logger.warning.assert_called_once_with("No services registered to start")


@pytest.mark.asyncio
async def test_stop_all_with_services():
    """Test stop_all method with registered services."""
    # Create manager
    manager = EventServiceManager()
    manager.logger = MagicMock()

    # Create mock services
    service1 = MockEventService()
    service2 = MockEventService()

    # Register services
    manager.register(service1)
    manager.register(service2)

    # Call method
    await manager.stop_all()

    # Verify results
    service1._stop_mock.assert_called_once()
    service2._stop_mock.assert_called_once()
    manager.logger.info.assert_called_once_with("Stopping 2 service(s) (MockEventService, MockEventService)")


@pytest.mark.asyncio
async def test_stop_all_no_services():
    """Test stop_all method with no registered services."""
    # Create manager
    manager = EventServiceManager()
    manager.logger = MagicMock()

    # Call method
    await manager.stop_all()

    # Verify results
    manager.logger.warning.assert_called_once_with("No services registered to stop")


@pytest.mark.asyncio
async def test_start_all_calls_gather():
    """Test that start_all calls asyncio.gather with service coroutines."""
    # Create manager
    manager = EventServiceManager()
    manager.logger = MagicMock()

    # Create mock services
    service1 = MockEventService()
    service2 = MockEventService()

    # Register services
    manager.register(service1)
    manager.register(service2)

    # Instead of mocking asyncio.gather, we'll intercept the coroutines
    # that would be passed to it and await them directly
    original_gather = asyncio.gather

    async def mock_gather(*coros):
        # Ensure all coroutines are awaited
        for coro in coros:
            await coro
        return None

    # Patch asyncio.gather with our mock that awaits all coroutines
    with patch("smib.events.services.asyncio.gather", mock_gather):
        # Call the actual start_all method
        await manager.start_all()

        # Verify that the services are in the manager
        assert len(manager._services) == 2
        assert service1 in manager._services
        assert service2 in manager._services

        # Verify that the start methods were called
        service1._start_mock.assert_called_once()
        service2._start_mock.assert_called_once()


@pytest.mark.asyncio
async def test_stop_all_calls_gather():
    """Test that stop_all calls asyncio.gather with service coroutines."""
    # Create manager
    manager = EventServiceManager()
    manager.logger = MagicMock()

    # Create mock services
    service1 = MockEventService()
    service2 = MockEventService()

    # Register services
    manager.register(service1)
    manager.register(service2)

    # Instead of mocking asyncio.gather, we'll intercept the coroutines
    # that would be passed to it and await them directly
    original_gather = asyncio.gather

    async def mock_gather(*coros):
        # Ensure all coroutines are awaited
        for coro in coros:
            await coro
        return None

    # Patch asyncio.gather with our mock that awaits all coroutines
    with patch("smib.events.services.asyncio.gather", mock_gather):
        # Call the actual stop_all method
        await manager.stop_all()

        # Verify that the services are in the manager
        assert len(manager._services) == 2
        assert service1 in manager._services
        assert service2 in manager._services

        # Verify that the stop methods were called
        service1._stop_mock.assert_called_once()
        service2._stop_mock.assert_called_once()
