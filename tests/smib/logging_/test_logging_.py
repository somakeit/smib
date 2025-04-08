import pytest
import logging
import importlib
from unittest.mock import patch


@pytest.fixture(autouse=True)
def reload_logging_config():
    """
    Fixture to dynamically reset and reload the logging system
    before each test, ensuring clean isolation for handlers and configuration.
    """
    # Shutdown existing logging state
    logging.shutdown()
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)


@patch("smib.utilities.environment.is_running_in_docker", return_value=False)
def test_logging_config_non_docker(mock_is_running_in_docker):
    """
    Test that the LOGGING_CONFIG uses the 'default' formatter when not running in Docker.
    """
    with patch("smib.utilities.environment.is_running_in_docker", return_value=False):
        import smib.logging_
        importlib.reload(smib.logging_)  # Dynamically reload the module after mock is applied
        smib.logging_.initialise_logging()  # Reinitialize the logger

    assert not mock_is_running_in_docker()  # Ensure mocked return value is False
    assert smib.logging_.LOGGING_CONFIG["handlers"]["console"]["formatter"] == "default"


@patch("smib.utilities.environment.is_running_in_docker", return_value=True)
def test_logging_config_in_docker(mock_is_running_in_docker):
    """
    Test that the LOGGING_CONFIG uses the 'docker' formatter when running in Docker.
    """
    with patch("smib.utilities.environment.is_running_in_docker", return_value=True):
        import smib.logging_
        importlib.reload(smib.logging_)  # Dynamically reload the module after mock
        smib.logging_.initialise_logging()  # Reinitialize the logger

    assert mock_is_running_in_docker()  # Ensure mocked return value is True
    assert smib.logging_.LOGGING_CONFIG["handlers"]["console"]["formatter"] == "docker"


@patch("logging.config.dictConfig")
def test_initialise_logging_applies_config(mock_dict_config):
    """
    Test that initialise_logging calls logging.config.dictConfig with LOGGING_CONFIG.
    """
    import smib.logging_
    importlib.reload(smib.logging_)  # Reload the module to reset the configuration
    smib.logging_.initialise_logging()

    mock_dict_config.assert_called_once_with(smib.logging_.LOGGING_CONFIG)


@pytest.mark.parametrize(
    "logger_name,log_level",
    [
        ("smib", logging.DEBUG),
        ("slack_bolt", logging.WARNING),
        ("slack_sdk", logging.WARNING),
        ("asyncio", logging.WARNING),
    ]
)
def test_logger_levels(logger_name, log_level):
    """
    Test that the loggers are configured with the correct levels.
    """
    import smib.logging_
    logger = logging.getLogger(logger_name)
    assert logger.level == log_level


@patch("logging.StreamHandler.emit")
def test_logging_output(mock_emit):
    """
    Test that logging outputs messages only once and adheres to the configuration.
    """
    # Dynamically reload and reinitialize logging
    import smib.logging_
    importlib.reload(smib.logging_)
    smib.logging_.initialise_logging()

    # Get the logger for the test
    logger = logging.getLogger("smib")

    # Deduplicate handlers if necessary (to avoid duplicate emit calls)
    while len(logger.handlers) > 1:
        logger.removeHandler(logger.handlers[-1])

    # Log a test message
    logger.info("Test message")

    # Assert `emit` was called exactly once
    mock_emit.assert_called_once()
    emitted_record = mock_emit.call_args[0][0]
    assert "Test message" in emitted_record.msg
    assert emitted_record.levelname == "INFO"
