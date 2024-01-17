"""Test the archive module."""

import os
from pathlib import Path

import pytest

from workflow.definitions.work import Work
from workflow.lifecycle.archive import http, posix, run, s3

WORKSPACE = {
    "archive": {
        "mounts": {
            "local": "/",
        }
    },
    "config": {
        "archive": {
            "plots": {
                "methods": [
                    "bypass",
                    "copy",
                    "delete",
                    "move",
                ],
                "storage": "s3",
            },
            "products": {
                "methods": [
                    "bypass",
                    "copy",
                    "delete",
                    "move",
                ],
                "storage": "posix",
            },
            "results": True,
        },
        "slack": None,
    },
    "http": {
        "baseurls": {
            "buckets": "http://localhost:8001",
            "loki": "http://localhost:8005/loki/api/v1/push",
            "minio": "http://localhost:8005",
            "pipelines": "http://localhost:8003",
            "products": "http://localhost:8004",
            "results": "http://localhost:8002",
        }
    },
    "sites": ["local"],
    "workspace": "testing",
}


@pytest.fixture
def work():
    """Return a Work instance."""
    test_plot = Path("test_plot.txt")
    test_product = Path("test_product.txt")
    test_plot.touch()
    test_product.touch()
    yield Work(
        user="tester",
        site="local",
        pipeline="test-pipeline",
        id="pytest",
        plots=[test_plot.as_posix()],
        products=[test_product.as_posix()],
    )
    test_plot.unlink(missing_ok=True)
    test_product.unlink(missing_ok=True)


def test_s3_env_vars_set():
    """Test the environment for S3 vars."""
    assert os.getenv("WORKFLOW_S3_ENDPOINT") == "play.min.io"
    assert os.getenv("WORKFLOW_S3_ACCESS_KEY") == "Q3AM3UQ867SPQQA43P2F"
    assert (
        os.getenv("WORKFLOW_S3_SECRET_KEY")
        == "zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG"
    )


def test_run_archive(work):
    """Test the run function."""
    run(work, WORKSPACE)


class TestS3:
    """Test S3 archive methods."""

    def test_s3_bypass(self):
        """Test the bypass method."""
        assert s3.bypass(Path("none"), []) is True

    def test_s3_copy(self):
        """Test the copy method."""
        pass

    def test_s3_delete(self):
        """Test the delete method."""
        with pytest.raises(NotImplementedError):
            s3.delete(Path("none"), [])

    def test_s3_move(self):
        """Test the move method."""
        pass

    def test_s3_permissions(self):
        """Test the permissions method."""
        with pytest.raises(NotImplementedError):
            s3.permissions(Path("none"), [])


class TestPosix:
    """Test POSIX archive methods."""

    def test_posix_bypass(self):
        """Test the bypass method."""
        assert posix.bypass(Path("none"), []) is True

    def test_posix_copy(self):
        """Test the copy method."""
        pass

    def test_posix_delete(self):
        """Test the delete method."""
        pass

    def test_posix_move(self):
        """Test the move method."""
        pass

    def test_posix_permissions(self):
        """Test the permissions method."""
        pass


class TestHttp:
    """Test HTTP archive methods."""

    def test_http_bypass(self):
        """Test the bypass method."""
        assert http.bypass(Path("none"), []) is True

    def test_http_copy(self):
        """Test the copy method."""
        with pytest.raises(NotImplementedError):
            http.copy(Path("none"), [])

    def test_http_delete(self):
        """Test the delete method."""
        with pytest.raises(NotImplementedError):
            http.delete(Path("none"), [])

    def test_http_move(self):
        """Test the move method."""
        with pytest.raises(NotImplementedError):
            http.move(Path("none"), [])

    def test_http_permissions(self):
        """Test the permissions method."""
        with pytest.raises(NotImplementedError):
            http.permissions(Path("none"), [])
