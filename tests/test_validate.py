from os import chmod

import pytest

from workflow.utils.validate import command, function


def test_validate_function():
    """Test the validate function function."""
    result = function("os.chmod")
    assert result == chmod

    # Test function import error
    with pytest.raises(ImportError):
        function("os.path")


def test_validate_command():
    """Test the validate command function."""
    result = command("ls")
    assert result is True

    # Test invalid command
    result = command("invalid_command")
    assert result is False
