import asyncio
import logging
import signal
import sys
from typing import Optional

# Global shutdown event
_shutdown_event: Optional[asyncio.Event] = None


def get_shutdown_event() -> asyncio.Event:
    """Get the global shutdown event."""
    global _shutdown_event
    if _shutdown_event is None:
        _shutdown_event = asyncio.Event()
    return _shutdown_event


def register_signal_handlers() -> None:
    """Register signal handlers for graceful shutdown."""
    logger = logging.getLogger(__name__)
    
    def handle_sigterm(*args):
        """Handle SIGTERM by setting the shutdown event."""
        logger.info("Received SIGTERM signal")
        # Set the shutdown event
        shutdown_event = get_shutdown_event()
        shutdown_event.set()

    if sys.platform == 'win32':
        # Windows-specific signal handling
        signal.signal(signal.SIGTERM, handle_sigterm)
        logger.debug("Registered SIGTERM handler (Windows)")
    else:
        # Unix-like systems signal handling
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, handle_sigterm)
        logger.debug("Registered SIGTERM handler (Unix)")