import asyncio
import logging
import signal
import sys


def register_signal_handlers() -> None:
    """Register signal handlers for graceful shutdown."""
    logger = logging.getLogger(__name__)
    
    def handle_sigterm(*args):
        """Handle SIGTERM by raising SystemExit, which will trigger cleanup."""
        logger.info("Received SIGTERM signal")
        raise SystemExit("SIGTERM received")

    if sys.platform == 'win32':
        # Windows-specific signal handling
        signal.signal(signal.SIGTERM, handle_sigterm)
        logger.debug("Registered SIGTERM handler (Windows)")
    else:
        # Unix-like systems signal handling
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, handle_sigterm)
        logger.debug("Registered SIGTERM handler (Unix)")