import pytest
from enum import StrEnum

from smib.events.handlers import BoltRequestMode


def test_bolt_request_mode_enum():
    """Test BoltRequestMode enum values."""
    # Verify BoltRequestMode is a StrEnum
    assert issubclass(BoltRequestMode, StrEnum)
    
    # Verify enum values
    assert BoltRequestMode.SOCKET_MODE == 'socket_mode'
    assert BoltRequestMode.HTTP == 'http_request'
    assert BoltRequestMode.SCHEDULED == 'scheduled'
    
    # Verify enum members
    assert len(BoltRequestMode) == 3
    assert BoltRequestMode.SOCKET_MODE in BoltRequestMode
    assert BoltRequestMode.HTTP in BoltRequestMode
    assert BoltRequestMode.SCHEDULED in BoltRequestMode
    
    # Verify string comparison works
    assert BoltRequestMode.SOCKET_MODE == 'socket_mode'
    assert 'socket_mode' == BoltRequestMode.SOCKET_MODE
    assert BoltRequestMode.HTTP == 'http_request'
    assert 'http_request' == BoltRequestMode.HTTP
    assert BoltRequestMode.SCHEDULED == 'scheduled'
    assert 'scheduled' == BoltRequestMode.SCHEDULED