"""Test the workspace CLI commands."""

import os

from click.testing import CliRunner

from workflow import CONFIG_PATH, DEFAULT_WORKSPACE_PATH
from workflow.cli.workspace import ls, set


class TestWorkspaceCLI:
    def test_workspace_ls(self):
        runner = CliRunner()
        result = runner.invoke(ls)
        assert result.exit_code == 0
        assert "From Workflow Python Module" in result.output
        assert "development" in result.output

    def test_workspace_set(self):
        runner = CliRunner()
        result = runner.invoke(set, ["development"])
        assert result.exit_code == 0
        assert "Locating workspace development" in result.output
        assert "Workspace development set to active" in result.output
        # ? Check the default folder only contains the active workspace file
        entries = os.listdir(CONFIG_PATH)
        files = [
            CONFIG_PATH / entry
            for entry in entries
            if os.path.isfile(os.path.join(CONFIG_PATH, entry))
        ]
        files = [f.as_posix() for f in files]
        assert files == [DEFAULT_WORKSPACE_PATH.as_posix()]
        # ? Re set workspace for other tests
        result = runner.invoke(set, ["development"])
