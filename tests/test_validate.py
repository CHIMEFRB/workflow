from os import chmod
from typing import Any, Dict

import pytest

from workflow.utils.validate import command, function, validate_deployments


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


def test_validate_deployments(config_with_deployments: Dict[str, Any]):
    """Tests the validate_deployment function."""
    unused, orphaned = validate_deployments(config=config_with_deployments)
    assert unused
    assert orphaned
    assert unused == ["ld1", "ld2", "ld4"]
    orphaned.sort()
    assert orphaned == ["echo", "printenv-2", "uname"]
