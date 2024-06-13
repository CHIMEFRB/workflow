"""Test the workspace CLI commands."""

import json
import os
from pathlib import Path

import yaml
from click.testing import CliRunner

from workflow import CONFIG_PATH, DEFAULT_WORKSPACE_PATH, workspaces
from workflow.cli.run import run
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
        assert DEFAULT_WORKSPACE_PATH.as_posix() in files
        # ? Re set workspace for other tests
        result = runner.invoke(set, ["development"])

    def test_workflow_run_help(self):
        runner = CliRunner()
        result = runner.invoke(run, ["--help"])
        assert result.exit_code == 0

    def test_workflow_run_execution(self):
        runner = CliRunner()
        result = runner.invoke(
            run, ["--site=local", "--lives=1", "--sleep=1", "some-pipeline-name"]
        )
        assert result.exit_code == 0
        # Test execution with tags, parent
        result = runner.invoke(
            run,
            [
                "--site=local",
                "--lives=1",
                "--sleep=1",
                "--tag=tag1",
                "--tag=tag2",
                "--parent=parent-pipeline-name",
                "some-pipeline-name",
            ],
        )

    def test_workflow_run_execution_with_runspace(self):
        runner = CliRunner()
        directory = Path(workspaces.__file__).parent
        devspace = directory / "development.yml"
        # Open and read in the yaml file
        with open(devspace) as file:
            data = yaml.safe_load(file)
        # Convert the data to runspace json configuration
        runspace = json.dumps(data)
        result = runner.invoke(
            run,
            [
                "--site=local",
                "--lives=1",
                "--sleep=1",
                f"--runspace={runspace}",
                "some-pipeline-name",
            ],
        )
        assert result.exit_code == 0
