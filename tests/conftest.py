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


@pytest.fixture(autouse=True, scope="function")
def config_with_deployments():
    """Return config with deployments for testing."""
    return {
        "version": "2",
        "name": "example_deployments",
        "defaults": {"user": "test", "site": "local"},
        "deployments": [
            {
                "name": "ld1",
                "site": "local",
                "image": "workflow_local_112312",
                "sleep": 1,
                "resources": {"cores": 2, "ram": "1G"},
                "replicas": 2,
            },
            {
                "name": "ld2",
                "site": "local",
                "sleep": 1,
                "image": "workflow_local_123123",
                "resources": {"cores": 4, "ram": "2G"},
                "replicas": 1,
            },
            {
                "name": "ld3",
                "site": "local",
                "sleep": 1,
                "image": "workflow_local",
                "resources": {"cores": 4, "ram": "2G"},
                "replicas": 1,
            },
            {
                "name": "ld4",
                "site": "local",
                "sleep": 1,
                "image": "workflow_local",
                "resources": {"cores": 4, "ram": "2G"},
                "replicas": 1,
            },
        ],
        "pipeline": {
            "steps": [
                {"name": "echo", "stage": 1, "work": {"command": ["ls", "-lah"]}},
                {"name": "uname", "stage": 2, "work": {"command": ["uname", "-a"]}},
                {
                    "name": "printenv",
                    "runs_on": "ld3",
                    "stage": 3,
                    "work": {"command": ["printenv"]},
                },
                {
                    "name": "printenv-2",
                    "stage": 4,
                    "work": {"command": ["printenv", "--version"]},
                },
            ]
        },
    }
