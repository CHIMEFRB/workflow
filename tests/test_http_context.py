"""Test the HTTPContext object."""

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
                "matrix": {"event": [123456, 654321], "site": ["chime", "canfar"]},
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
        HTTPContext()

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
        response = http.configs.get_configs(config_name=None)
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
