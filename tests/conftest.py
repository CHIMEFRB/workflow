"""pytest configuration file."""
from click.testing import CliRunner

from workflow.cli.main import cli as workflow


def pytest_configure(config):
    """Initailize pytest configuration.

    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    runner = CliRunner()
    runner.invoke(workflow, ["workspace", "set", "development"])
