"""pytest configuration file."""

import pytest
from click.testing import CliRunner

from workflow.cli.main import cli as workflow


@pytest.fixture(autouse=True, scope="function")
def set_testing_workspace():
    """Initailize testing workspace."""
    runner = CliRunner()
    runner.invoke(workflow, ["workspace", "set", "development"])
    return True
