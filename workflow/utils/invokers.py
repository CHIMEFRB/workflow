"""Invoker functions to call click commands."""

from click.testing import CliRunner, Result

from workflow.cli.workspace import unset


def call_unset() -> Result:
    """Calls the unset command from code.

    Returns
    -------
    str
        CliRunner output.
    """
    runner = CliRunner()
    unset_result = runner.invoke(unset)
    return unset_result
