"""Test the HTTPContext object."""

import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from workflow.cli.workspace import set, unset
from workflow.http.context import HTTPContext

config = {
    "version": "1",
    "name": "demo",
    "defaults": {"user": "test"},
    "pipeline": {
        "steps": [
            {
                "name": "stage-1-a",
                "stage": 1,
                "matrix": {"event": [123456, 654321], "site": ["local"]},
                "work": {
                    "site": "${{ matrix.site }}",
                    "command": ["ls", "${{ matrix.event }}"],
                },
            },
        ],
    },
}


class TestHTTPContext:
    def test_can_be_instantiated(self):
        """Test that the HTTPContext object can be instantiated."""
        http = HTTPContext()
        assert http

    def test_cannot_be_instantiated_without_workspace(self):
        """Test that the HTTPContext object cannot be instantiated without workspace."""
        runner = CliRunner()
        # ? Set Workspace
        runner.invoke(unset)
        with pytest.raises(ValidationError):
            HTTPContext()
        runner.invoke(set, ["development"])

    def test_clients_connect_to_base_url(self):
        """Tests HTTPContext.clients have connection to their proper backend."""
        http = HTTPContext()
        assert isinstance(http.buckets.info(), dict)
        assert isinstance(http.results.info(), dict)
        assert isinstance(http.configs.info(), dict)
        assert isinstance(http.pipelines.info(), dict)

    def test_http_configs_deploy(self):
        http = HTTPContext()
        response = http.configs.deploy(config)
        assert isinstance(response, dict)
        assert "config" in response.keys()
        assert "pipelines" in response.keys()

    def test_http_configs_list(self):
        http = HTTPContext()
        response = http.configs.get_configs(name=None)
        assert isinstance(response, list)

    def test_http_configs_count(self):
        http = HTTPContext()
        response = http.configs.count()
        assert isinstance(response, dict)

    def test_http_configs_remove_process(self):
        http = HTTPContext()
        # ? Post
        post_response = http.configs.deploy(config)
        stop_response = http.configs.stop(config["name"], post_response["config"])
        assert stop_response["stopped_config"] == post_response["config"]
        remove_response = http.configs.remove(config["name"], post_response["config"])
        assert remove_response.status_code == 204

    def test_http_pipelines_list(self):
        http = HTTPContext()
        response = http.pipelines.list_pipelines()
        assert isinstance(response, list)

    def test_http_pipelines_get(self):
        http = HTTPContext()
        count_response = http.pipelines.count()
        response = http.pipelines.get_pipelines(name="demo", query={}, projection={})
        assert count_response
        assert isinstance(response, list)
