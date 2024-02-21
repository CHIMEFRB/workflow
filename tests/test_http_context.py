"""Test the HTTPContext object."""
from workflow.http.context import HTTPContext


class TestHTTPContext:
    def test_can_be_instantiated(self):
        """Test that the HTTPContext object can be instantiated."""
        HTTPContext()

    def test_clients_connect_to_base_url(self):
        """Tests HTTPContext.clients have connection to their proper backend."""
        http = HTTPContext()
        assert isinstance(http.buckets.info(), dict)
        # TODO test results and pipelines
