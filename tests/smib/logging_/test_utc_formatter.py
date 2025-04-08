import logging
import time
from datetime import datetime, timezone, UTC
from unittest.mock import MagicMock
from smib.logging_.utc_formatter import UTCFormatter


def test_utc_formatter_format_time_with_default_datefmt():
    """Test UTCFormatter's formatTime method with default datefmt."""
    formatter = UTCFormatter()

    # Mock a log record
    mock_record = MagicMock()
    mock_record.created = 1680307200.0  # Example UNIX timestamp (March 31, 2023, 12:00 UTC)

    formatted_time = formatter.formatTime(mock_record)
    expected_time = datetime.fromtimestamp(1680307200.0, tz=timezone.utc).isoformat()

    assert formatted_time == expected_time, (
        f"Expected {expected_time}, but got {formatted_time}"
    )


def test_utc_formatter_format_time_with_custom_datefmt():
    """Test UTCFormatter's formatTime method using a custom datefmt."""
    formatter = UTCFormatter()

    # Mock a log record
    mock_record = MagicMock()
    mock_record.created = 1680307200.0  # Example UNIX timestamp (March 31, 2023, 12:00 UTC)

    # Attempt to use a custom datefmt (not supported directly since formatTime ignores it)
    formatted_time = formatter.formatTime(mock_record, datefmt="%Y-%m-%d %H:%M:%S %Z")
    expected_time = datetime.fromtimestamp(1680307200.0, tz=timezone.utc).isoformat()

    # Since the `datefmt` argument in UTCFormatter is not used, the default isoformat is expected
    assert formatted_time == expected_time, (
        f"Expected {expected_time}, but got {formatted_time}"
    )


def test_utc_formatter_format_time_with_mock_logger():
    """Test the UTCFormatter by integrating it with a logger."""
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)

    # Add the UTCFormatter with a StreamHandler to the logger
    stream_handler = logging.StreamHandler()
    formatter = UTCFormatter(fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Create a real log record
    log_record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_path",
        lineno=42,
        msg="Test log message",
        args=None,
        exc_info=None,
    )
    log_record.created = time.time()  # Set custom UNIX timestamp for the test
    log_record.ct = log_record.created  # Set custom UNIX timestamp for the test

    # Format the record using the StreamHandler with the UTCFormatter
    formatted_message = stream_handler.format(log_record)

    # Verify the formatted message contains the correct UTC timestamp in ISO format
    expected_time = datetime.fromtimestamp(log_record.created, tz=UTC).isoformat()
    assert expected_time in formatted_message, (
        f"Expected log message to contain the correct UTC timestamp. Got: {formatted_message}"
    )
