"""Test the HTTPContext object."""

import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from workflow.cli.workspace import set, unset
from workflow.http.context import HTTPContext


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

    @pytest.mark.skip
    def test_clients_connect_to_base_url(self):
        """Tests HTTPContext.clients have connection to their proper backend."""
        http = HTTPContext()
        assert isinstance(http.buckets.info(), dict)
        # TODO test results and pipelines
