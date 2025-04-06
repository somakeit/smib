from unittest.mock import patch

from smib.utilities.environment import is_running_in_docker


def test_is_running_in_docker_file_present():
    """Test is_running_in_docker true by simulating /.dockerenv's existence."""
    # Mocking Path's internal implementation to make /.dockerenv "exist"
    with patch("pathlib.Path.open", create=True), patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True  # Simulate file exists
        assert is_running_in_docker() is True


def test_is_running_in_docker_file_absent():
    """Test is_running_in_docker false when /.dockerenv doesn't exist."""
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False  # Simulate the file does not exist
        assert is_running_in_docker() is False
